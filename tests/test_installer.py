"""Behavior tests for ``sync_ai_rules.py`` explicit-ownership distribution.

The tests run the real installer against an isolated temporary ``HOME`` and a
temporary fixture source tree, so they never touch the operator's configuration.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests import harness
from tests.harness import InstallerFixture

SKILL_PRIMARY = harness.SKILL_DIRS[0]
BLOCK_BEGIN = "<!-- BEGIN awesome-ai-prompts (managed) -->"
BLOCK_END = "<!-- END awesome-ai-prompts -->"


class InstallerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = InstallerFixture(Path(self._tmp.name))
        self.fx.set_doc("rules.md", "# Rules\n\nBody.\n")
        self.fx.set_skill(
            "alpha",
            {"SKILL.md": "---\nname: alpha\ndescription: A.\n---\nbody\n"},
        )
        self.fx.set_command(
            "cmd.md", "---\ndescription: C.\nagent: plan\n---\nbody\n"
        )


class EmptyInstallationTests(InstallerTestCase):
    def test_empty_installation_populates_every_target(self) -> None:
        result = self.fx.run()
        self.assertEqual(0, result.returncode, result.stderr)

        for agent in harness.RULE_PATHS:
            text = self.fx.rules(agent).read_text(encoding="utf-8")
            self.assertIn(BLOCK_BEGIN, text)
            self.assertIn(BLOCK_END, text)
            self.assertIn("# Rules", text)

        for agent in harness.COMMAND_DIRS:
            self.assertTrue((self.fx.commands_dir(agent) / "cmd.md").is_file())

        for directory in harness.SKILL_DIRS:
            self.assertTrue(
                (self.fx.skill(directory, "alpha") / "SKILL.md").is_file()
            )

        self.assertTrue(self.fx.manifest_file().is_file())

    def test_skill_sidecars_excluded_only_at_skill_root(self) -> None:
        self.fx.set_skill(
            "alpha",
            {
                "SKILL.md": "---\nname: alpha\ndescription: A.\n---\nbody\n",
                "agents/helper.md": "sidecar\n",
                "nested/agents/keep.md": "nested\n",
                ".DS_Store": "junk\n",
            },
        )
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.skill(SKILL_PRIMARY, "alpha")
        self.assertTrue((target / "SKILL.md").is_file())
        self.assertFalse((target / "agents").exists())
        self.assertTrue((target / "nested" / "agents" / "keep.md").is_file())
        self.assertFalse((target / ".DS_Store").exists())

    def test_repeated_runs_are_idempotent(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        first = {
            agent: self.fx.rules(agent).read_bytes()
            for agent in harness.RULE_PATHS
        }
        self.assertEqual(0, self.fx.run().returncode)
        second = {
            agent: self.fx.rules(agent).read_bytes()
            for agent in harness.RULE_PATHS
        }
        self.assertEqual(first, second)


class ManagedSkillTests(InstallerTestCase):
    def test_managed_skill_is_updated_in_place(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.skill(SKILL_PRIMARY, "alpha") / "SKILL.md"
        self.fx.set_skill(
            "alpha",
            {"SKILL.md": "---\nname: alpha\ndescription: A.\n---\nversion two\n"},
        )
        self.assertEqual(0, self.fx.run().returncode)
        self.assertIn("version two", target.read_text(encoding="utf-8"))

    def test_local_drift_of_managed_skill_is_refused_then_forced(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.skill(SKILL_PRIMARY, "alpha") / "SKILL.md"
        target.write_text("LOCAL DRIFT\n", encoding="utf-8")

        refused = self.fx.run()
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("locally modified skill", refused.stderr)
        self.assertEqual("LOCAL DRIFT\n", target.read_text(encoding="utf-8"))

        forced = self.fx.run("--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertNotIn("LOCAL DRIFT", target.read_text(encoding="utf-8"))

    def test_removed_managed_skill_is_pruned_and_unmanaged_survives(self) -> None:
        self.fx.set_skill(
            "beta",
            {"SKILL.md": "---\nname: beta\ndescription: B.\n---\nbody\n"},
        )
        self.assertEqual(0, self.fx.run().returncode)

        unmanaged = self.fx.skill(SKILL_PRIMARY, "gamma")
        unmanaged.mkdir(parents=True)
        (unmanaged / "SKILL.md").write_text("GAMMA\n", encoding="utf-8")

        self.fx.remove_skill("beta")
        self.assertEqual(0, self.fx.run().returncode)

        for directory in harness.SKILL_DIRS:
            self.assertFalse(self.fx.skill(directory, "beta").exists())
        self.assertTrue((unmanaged / "SKILL.md").is_file())
        managed = self.fx.manifest()["files"]
        self.assertNotIn(".agents/skills/gamma/SKILL.md", managed)

    def test_unmanaged_skill_collision_is_refused(self) -> None:
        clash = self.fx.home / Path(".agents/skills") / "alpha"
        clash.mkdir(parents=True)
        (clash / "SKILL.md").write_text("LOCAL\n", encoding="utf-8")

        result = self.fx.run()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("refusing to replace unmanaged skill", result.stderr)
        self.assertEqual("LOCAL\n", (clash / "SKILL.md").read_text(encoding="utf-8"))


class RulesTests(InstallerTestCase):
    def test_unmanaged_rules_file_is_preserved_with_managed_block(self) -> None:
        for agent in harness.RULE_PATHS:
            path = self.fx.rules(agent)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# LOCAL RULES\n", encoding="utf-8")

        result = self.fx.run()
        self.assertEqual(0, result.returncode, result.stderr)

        for agent in harness.RULE_PATHS:
            text = self.fx.rules(agent).read_text(encoding="utf-8")
            self.assertIn("# LOCAL RULES", text)
            self.assertIn(BLOCK_BEGIN, text)
            self.assertIn("# Rules", text)

    def test_managed_rules_block_is_refreshed_preserving_surrounding_content(
        self,
    ) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        path = self.fx.rules("opencode")
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "# Personal\n\n" + text + "\n# Trailing\n", encoding="utf-8"
        )
        self.fx.set_doc("rules.md", "# Rules\n\nUpdated body.\n")

        self.assertEqual(0, self.fx.run().returncode)

        updated = path.read_text(encoding="utf-8")
        self.assertIn("# Personal", updated)
        self.assertIn("# Trailing", updated)
        self.assertIn("Updated body.", updated)
        self.assertEqual(1, updated.count(BLOCK_BEGIN))
        self.assertEqual(1, updated.count(BLOCK_END))

    def test_locally_modified_rules_block_is_refused_then_forced(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        path = self.fx.rules("opencode")
        path.write_text(
            path.read_text(encoding="utf-8").replace("Body.", "LOCAL EDIT"),
            encoding="utf-8",
        )

        refused = self.fx.run()
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("locally modified rules block", refused.stderr)
        self.assertIn("LOCAL EDIT", path.read_text(encoding="utf-8"))

        forced = self.fx.run("--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("LOCAL EDIT", text)
        self.assertIn("Body.", text)


class CommandTests(InstallerTestCase):
    def test_unmanaged_command_is_refused(self) -> None:
        for agent in harness.COMMAND_DIRS:
            directory = self.fx.commands_dir(agent)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "cmd.md").write_text("LOCAL COMMAND\n", encoding="utf-8")

        result = self.fx.run()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("refusing to replace unmanaged command", result.stderr)
        for agent in harness.COMMAND_DIRS:
            self.assertEqual(
                "LOCAL COMMAND\n",
                (self.fx.commands_dir(agent) / "cmd.md").read_text(encoding="utf-8"),
            )

    def test_managed_command_is_updated_and_obsolete_is_removed(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        unmanaged = self.fx.commands_dir("opencode") / "user.md"
        unmanaged.write_text("USER\n", encoding="utf-8")

        self.fx.set_command(
            "cmd.md", "---\ndescription: C2.\nagent: plan\n---\nversion two\n"
        )
        self.assertEqual(0, self.fx.run().returncode)
        for agent in harness.COMMAND_DIRS:
            self.assertIn(
                "version two",
                (self.fx.commands_dir(agent) / "cmd.md").read_text(encoding="utf-8"),
            )

        self.fx.remove_command("cmd.md")
        self.assertEqual(0, self.fx.run().returncode)
        for agent in harness.COMMAND_DIRS:
            self.assertFalse((self.fx.commands_dir(agent) / "cmd.md").exists())
        self.assertEqual("USER\n", unmanaged.read_text(encoding="utf-8"))

    def test_locally_modified_managed_command_is_refused_then_forced(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.commands_dir("opencode") / "cmd.md"
        target.write_text("LOCAL COMMAND\n", encoding="utf-8")

        refused = self.fx.run()
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("locally modified command", refused.stderr)
        self.assertEqual("LOCAL COMMAND\n", target.read_text(encoding="utf-8"))

        forced = self.fx.run("--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertIn("description: C.", target.read_text(encoding="utf-8"))

    def test_missing_managed_command_is_recreated(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.commands_dir("opencode") / "cmd.md"
        target.unlink()

        self.assertEqual(0, self.fx.run().returncode)
        self.assertTrue(target.is_file())


class ManifestTests(InstallerTestCase):
    def test_manifest_records_repo_and_content_hashes(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        manifest = self.fx.manifest()

        self.assertEqual(1, manifest["version"])
        self.assertEqual("unknown", manifest["repo"])

        files = manifest["files"]
        self.assertIn(".config/opencode/commands/cmd.md", files)
        self.assertIn(".agents/skills/alpha/SKILL.md", files)
        self.assertEqual(64, len(files[".agents/skills/alpha/SKILL.md"]["sha256"]))

        blocks = manifest["blocks"]
        for agent in harness.RULE_PATHS:
            self.assertIn(str(harness.RULE_PATHS[agent]), blocks)
            self.assertEqual(64, len(blocks[str(harness.RULE_PATHS[agent])]["sha256"]))


class LegacyMigrationTests(InstallerTestCase):
    def _seed_legacy_install(self) -> None:
        ai_rules = self.fx.home / ".ai-rules"
        ai_rules.mkdir(parents=True, exist_ok=True)
        (ai_rules / "installed").write_text("deadbeef\n", encoding="utf-8")
        (ai_rules / "managed-skills").write_text("alpha\n", encoding="utf-8")

        for agent in harness.RULE_PATHS:
            path = self.fx.rules(agent)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "<!-- awesome-ai-prompts deadbeef -->\n\n# Rules\n\nOLD\n",
                encoding="utf-8",
            )
        for agent in harness.COMMAND_DIRS:
            directory = self.fx.commands_dir(agent)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "cmd.md").write_text("OLD COMMAND\n", encoding="utf-8")
            (directory / "personal.md").write_text("MINE\n", encoding="utf-8")
        for directory in harness.SKILL_DIRS:
            skill = self.fx.skill(directory, "alpha")
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text("OLD SKILL\n", encoding="utf-8")

    def test_legacy_install_migrates_without_refusing(self) -> None:
        self._seed_legacy_install()

        result = self.fx.run()

        self.assertEqual(0, result.returncode, result.stderr)
        for agent in harness.RULE_PATHS:
            text = self.fx.rules(agent).read_text(encoding="utf-8")
            self.assertIn(BLOCK_BEGIN, text)
            self.assertNotIn("OLD", text)
        for agent in harness.COMMAND_DIRS:
            self.assertIn(
                "description: C.",
                (self.fx.commands_dir(agent) / "cmd.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "MINE\n",
                (self.fx.commands_dir(agent) / "personal.md").read_text(
                    encoding="utf-8"
                ),
            )
        for directory in harness.SKILL_DIRS:
            self.assertIn(
                "body",
                (self.fx.skill(directory, "alpha") / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
            )
        self.assertTrue(self.fx.manifest_file().is_file())
        self.assertFalse((self.fx.home / ".ai-rules" / "installed").exists())
        self.assertFalse((self.fx.home / ".ai-rules" / "managed-skills").exists())


class HomeIsolationTests(InstallerTestCase):
    def test_isolated_home_never_mutates_real_home(self) -> None:
        real_home = Path.home()
        before = harness.snapshot(real_home, harness.REAL_HOME_TARGETS)

        result = self.fx.run()

        after = harness.snapshot(real_home, harness.REAL_HOME_TARGETS)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, after)
        self.assertIn(str(self.fx.home), result.stdout)
        self.assertFalse((self.fx.home / ".ai-rules" / "src").exists())


class DryRunTests(InstallerTestCase):
    def test_dry_run_reports_plan_and_changes_nothing(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        before = harness.snapshot(self.fx.home, harness.INSTALL_TARGETS)

        self.fx.set_doc("rules.md", "# Rules\n\nChanged body.\n")
        self.fx.set_command(
            "new.md", "---\ndescription: N.\nagent: plan\n---\nnew\n"
        )
        self.fx.remove_command("cmd.md")

        result = self.fx.run("--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        output = result.stdout
        self.assertIn("dry run:", output)
        self.assertIn("create", output)
        self.assertIn("update", output)
        self.assertIn("remove", output)
        self.assertIn("unchanged", output)
        self.assertIn("new.md", output)
        self.assertIn("cmd.md", output)

        after = harness.snapshot(self.fx.home, harness.INSTALL_TARGETS)
        self.assertEqual(before, after)

        self.assertEqual(0, self.fx.run().returncode)
        self.assertIn("Changed body.", self.fx.rules("opencode").read_text())
        for agent in harness.COMMAND_DIRS:
            self.assertTrue((self.fx.commands_dir(agent) / "new.md").is_file())
            self.assertFalse((self.fx.commands_dir(agent) / "cmd.md").exists())

    def test_dry_run_reports_conflicts_without_failing(self) -> None:
        path = self.fx.commands_dir("opencode") / "cmd.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("LOCAL\n", encoding="utf-8")

        result = self.fx.run("--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("conflict", result.stdout)
        self.assertEqual("LOCAL\n", path.read_text(encoding="utf-8"))


class AgentSelectionTests(InstallerTestCase):
    def test_single_agent_limits_targets(self) -> None:
        result = self.fx.run("--agent", "claude")
        self.assertEqual(0, result.returncode, result.stderr)

        self.assertTrue(self.fx.rules("claude").is_file())
        for other in ("opencode", "codex", "pi"):
            self.assertFalse(self.fx.rules(other).exists())
        self.assertTrue((self.fx.commands_dir("claude") / "cmd.md").is_file())
        for other in ("opencode", "codex", "pi"):
            self.assertFalse(self.fx.commands_dir(other).exists())
        self.assertTrue(
            (self.fx.skill(Path(".claude/skills"), "alpha") / "SKILL.md").is_file()
        )
        self.assertFalse((self.fx.home / Path(".agents/skills")).exists())

    def test_multiple_agents_share_skills_directory(self) -> None:
        result = self.fx.run("--agent", "opencode", "--agent", "pi")
        self.assertEqual(0, result.returncode, result.stderr)

        self.assertTrue(self.fx.rules("opencode").is_file())
        self.assertTrue(self.fx.rules("pi").is_file())
        self.assertFalse(self.fx.rules("claude").exists())
        self.assertFalse(self.fx.rules("codex").exists())
        self.assertTrue(
            (self.fx.skill(harness.SKILL_DIRS[0], "alpha") / "SKILL.md").is_file()
        )
        self.assertFalse((self.fx.home / Path(".claude/skills")).exists())

    def test_unknown_agent_is_rejected(self) -> None:
        result = self.fx.run("--agent", "bogus")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unknown agent", result.stderr)

    def test_selected_run_leaves_other_agents_untouched(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        claude_rules = self.fx.rules("claude").read_bytes()
        claude_command = (self.fx.commands_dir("claude") / "cmd.md").read_bytes()

        self.assertEqual(0, self.fx.run("--agent", "opencode").returncode)

        self.assertEqual(claude_rules, self.fx.rules("claude").read_bytes())
        self.assertEqual(
            claude_command,
            (self.fx.commands_dir("claude") / "cmd.md").read_bytes(),
        )
        self.assertIn(".claude/CLAUDE.md", self.fx.manifest()["blocks"])


class RollbackTests(InstallerTestCase):
    def test_failed_mutation_rolls_back_every_change(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        self.fx.set_doc("rules.md", "# Rules\n\nChanged body.\n")

        # Occupy a command file path's parent with a regular file so the write
        # fails partway through the run, after the rules files are updated.
        commands = self.fx.commands_dir("opencode")
        shutil.rmtree(commands)
        commands.write_text("not a directory\n", encoding="utf-8")

        before = harness.snapshot(self.fx.home, harness.INSTALL_TARGETS)
        result = self.fx.run()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("rolled back", result.stderr)
        self.assertNotIn("Changed body.", self.fx.rules("opencode").read_text())
        after = harness.snapshot(self.fx.home, harness.INSTALL_TARGETS)
        self.assertEqual(before, after)


class UninstallTests(InstallerTestCase):
    def test_uninstall_removes_only_managed_content(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        user_command = self.fx.commands_dir("opencode") / "user.md"
        user_command.write_text("USER\n", encoding="utf-8")
        rules = self.fx.rules("opencode")
        rules.write_text(
            "# PERSONAL\n\n" + rules.read_text(encoding="utf-8"), encoding="utf-8"
        )

        result = self.fx.run("--uninstall")
        self.assertEqual(0, result.returncode, result.stderr)

        self.assertTrue(user_command.is_file())
        text = rules.read_text(encoding="utf-8")
        self.assertIn("# PERSONAL", text)
        self.assertNotIn(BLOCK_BEGIN, text)
        self.assertFalse(self.fx.manifest_file().exists())
        for agent in harness.COMMAND_DIRS:
            self.assertFalse((self.fx.commands_dir(agent) / "cmd.md").exists())
        for directory in harness.SKILL_DIRS:
            self.assertFalse(self.fx.skill(directory, "alpha").exists())

    def test_uninstall_keeps_locally_modified_file(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.commands_dir("opencode") / "cmd.md"
        target.write_text("LOCAL\n", encoding="utf-8")

        result = self.fx.run("--uninstall")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("LOCAL\n", target.read_text(encoding="utf-8"))
        self.assertTrue(self.fx.manifest_file().is_file())
        self.assertFalse((self.fx.commands_dir("claude") / "cmd.md").exists())

    def test_uninstall_force_removes_modified_file(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.commands_dir("opencode") / "cmd.md"
        target.write_text("LOCAL\n", encoding="utf-8")

        result = self.fx.run("--uninstall", "--force")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(target.exists())

    def test_uninstall_one_agent_leaves_others(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)

        result = self.fx.run("--uninstall", "--agent", "claude")
        self.assertEqual(0, result.returncode, result.stderr)

        self.assertFalse(self.fx.rules("claude").exists())
        self.assertTrue(self.fx.rules("opencode").is_file())
        self.assertFalse((self.fx.commands_dir("claude") / "cmd.md").exists())
        self.assertTrue((self.fx.commands_dir("opencode") / "cmd.md").is_file())
        self.assertTrue(
            (self.fx.skill(harness.SKILL_DIRS[0], "alpha") / "SKILL.md").is_file()
        )


class RestoreTests(InstallerTestCase):
    def test_uninstall_then_restore_round_trip(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        rules_before = self.fx.rules("opencode").read_bytes()
        command_before = (self.fx.commands_dir("opencode") / "cmd.md").read_bytes()
        skill_before = (
            self.fx.skill(SKILL_PRIMARY, "alpha") / "SKILL.md"
        ).read_bytes()

        self.assertEqual(0, self.fx.run("--uninstall").returncode)
        self.assertFalse(self.fx.manifest_file().exists())
        self.assertFalse(self.fx.rules("opencode").exists())
        self.assertFalse((self.fx.commands_dir("opencode") / "cmd.md").exists())

        result = self.fx.run("--restore", "latest")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(rules_before, self.fx.rules("opencode").read_bytes())
        self.assertEqual(
            command_before,
            (self.fx.commands_dir("opencode") / "cmd.md").read_bytes(),
        )
        self.assertEqual(
            skill_before,
            (self.fx.skill(SKILL_PRIMARY, "alpha") / "SKILL.md").read_bytes(),
        )
        self.assertTrue(self.fx.manifest_file().is_file())


class CheckTests(InstallerTestCase):
    @staticmethod
    def _entries(output: str, label: str) -> list[str]:
        prefix = f"  {label}"
        found: list[str] = []
        for line in output.splitlines():
            if line.startswith(prefix) and line[len(prefix) : len(prefix) + 1] == " ":
                found.append(line.split(None, 1)[1].strip())
        return found

    def test_clean_install_reports_ok_integrity(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        result = self.fx.run("--check")
        self.assertIn("repository", result.stdout)
        self.assertIn("integrity", result.stdout)
        self.assertIn("status     ok", result.stdout)
        self.assertEqual([], self._entries(result.stdout, "modified"))
        self.assertEqual([], self._entries(result.stdout, "missing"))
        self.assertEqual([], self._entries(result.stdout, "unexpected"))
        self.assertEqual([], self._entries(result.stdout, "obsolete"))

    def test_check_identifies_exact_modified_file(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.commands_dir("opencode") / "cmd.md"
        target.write_text("LOCAL EDIT\n", encoding="utf-8")

        result = self.fx.run("--check")
        self.assertNotEqual(0, result.returncode)
        modified = self._entries(result.stdout, "modified")
        self.assertEqual(1, len(modified))
        self.assertTrue(modified[0].endswith(".config/opencode/commands/cmd.md"))
        self.assertIn("drift detected", result.stdout)

    def test_check_identifies_missing_file(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        (self.fx.skill(SKILL_PRIMARY, "alpha") / "SKILL.md").unlink()

        result = self.fx.run("--check")
        self.assertNotEqual(0, result.returncode)
        missing = self._entries(result.stdout, "missing")
        self.assertTrue(any(path.endswith(".agents/skills/alpha/SKILL.md") for path in missing))
        self.assertIn("drift detected", result.stdout)

    def test_check_identifies_obsolete_artifact(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        self.fx.remove_command("cmd.md")

        result = self.fx.run("--check")
        self.assertNotEqual(0, result.returncode)
        obsolete = self._entries(result.stdout, "obsolete")
        self.assertEqual(4, len(obsolete))
        self.assertTrue(all(path.endswith("cmd.md") for path in obsolete))

    def test_check_identifies_unexpected_artifact(self) -> None:
        self.assertEqual(0, self.fx.run("--agent", "opencode").returncode)
        claude = self.fx.rules("claude")
        claude.parent.mkdir(parents=True, exist_ok=True)
        claude.write_text(
            BLOCK_BEGIN + "\n# Rules\n\nBody.\n" + BLOCK_END + "\n",
            encoding="utf-8",
        )

        result = self.fx.run("--check")
        self.assertNotEqual(0, result.returncode)
        unexpected = self._entries(result.stdout, "unexpected")
        self.assertTrue(any(path.endswith(".claude/CLAUDE.md") for path in unexpected))

    def test_check_reports_repository_and_integrity_separately(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        result = self.fx.run("--check")
        self.assertIn("repository", result.stdout)
        self.assertIn("integrity", result.stdout)
        self.assertLess(
            result.stdout.index("repository"), result.stdout.index("integrity")
        )


if __name__ == "__main__":
    unittest.main()
