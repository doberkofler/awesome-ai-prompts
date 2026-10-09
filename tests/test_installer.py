"""Characterization tests for the current ``sync_ai_rules.py`` behavior.

These tests pin the behavior that exists today so later phases can change it
deliberately. Behaviors that are known to be unsafe are flagged in the test
docstring with the phase that is expected to replace them.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests import harness
from tests.harness import InstallerFixture

SKILL_PRIMARY = harness.SKILL_DIRS[0]


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
            self.assertIn("awesome-ai-prompts", text)
            self.assertIn("# Rules", text)

        for agent in harness.COMMAND_DIRS:
            self.assertTrue((self.fx.commands_dir(agent) / "cmd.md").is_file())

        for directory in harness.SKILL_DIRS:
            self.assertTrue(
                (self.fx.skill(directory, "alpha") / "SKILL.md").is_file()
            )

        self.assertEqual(
            ["alpha"], self.fx.managed_skills_file().read_text().split()
        )
        self.assertTrue(self.fx.installed_state_file().is_file())

    def test_skill_sidecars_and_ds_store_are_excluded(self) -> None:
        self.fx.set_skill(
            "alpha",
            {
                "SKILL.md": "---\nname: alpha\ndescription: A.\n---\nbody\n",
                "agents/helper.md": "helper\n",
                ".DS_Store": "junk\n",
            },
        )
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.skill(SKILL_PRIMARY, "alpha")
        self.assertTrue((target / "SKILL.md").is_file())
        self.assertFalse((target / "agents").exists())
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

    def test_local_drift_of_managed_skill_is_overwritten(self) -> None:
        """Current behavior. Phase 3 should refuse until the user approves."""
        self.assertEqual(0, self.fx.run().returncode)
        target = self.fx.skill(SKILL_PRIMARY, "alpha") / "SKILL.md"
        target.write_text("LOCAL DRIFT\n", encoding="utf-8")
        self.assertEqual(0, self.fx.run().returncode)
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
        self.assertEqual(
            ["alpha"], self.fx.managed_skills_file().read_text().split()
        )

    def test_unmanaged_skill_collision_is_refused(self) -> None:
        clash = self.fx.home / Path(".agents/skills") / "alpha"
        clash.mkdir(parents=True)
        (clash / "SKILL.md").write_text("LOCAL\n", encoding="utf-8")

        result = self.fx.run()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("refusing to replace unmanaged skill", result.stderr)
        self.assertEqual("LOCAL\n", (clash / "SKILL.md").read_text(encoding="utf-8"))


class RulesAndCommandTests(InstallerTestCase):
    def test_unmanaged_rules_file_is_overwritten(self) -> None:
        """Current behavior. Phase 3 should refuse to replace unmanaged rules."""
        for agent in harness.RULE_PATHS:
            path = self.fx.rules(agent)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("LOCAL RULES\n", encoding="utf-8")

        self.assertEqual(0, self.fx.run().returncode)

        for agent in harness.RULE_PATHS:
            text = self.fx.rules(agent).read_text(encoding="utf-8")
            self.assertNotIn("LOCAL RULES", text)
            self.assertIn("# Rules", text)

    def test_managed_rules_file_is_refreshed(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        self.fx.set_doc("rules.md", "# Rules\n\nUpdated body.\n")
        self.assertEqual(0, self.fx.run().returncode)
        for agent in harness.RULE_PATHS:
            self.assertIn(
                "Updated body.", self.fx.rules(agent).read_text(encoding="utf-8")
            )

    def test_unmanaged_command_is_overwritten(self) -> None:
        """Current behavior. Phase 3 should refuse to replace unmanaged files."""
        for agent in harness.COMMAND_DIRS:
            directory = self.fx.commands_dir(agent)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "cmd.md").write_text("LOCAL COMMAND\n", encoding="utf-8")

        self.assertEqual(0, self.fx.run().returncode)

        for agent in harness.COMMAND_DIRS:
            text = (self.fx.commands_dir(agent) / "cmd.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("LOCAL COMMAND", text)
            self.assertIn("description: C.", text)

    def test_command_update_and_obsolete_command_retention(self) -> None:
        self.assertEqual(0, self.fx.run().returncode)
        self.fx.set_command(
            "cmd.md", "---\ndescription: C2.\nagent: plan\n---\nversion two\n"
        )
        self.assertEqual(0, self.fx.run().returncode)
        for agent in harness.COMMAND_DIRS:
            self.assertIn(
                "version two",
                (self.fx.commands_dir(agent) / "cmd.md").read_text(encoding="utf-8"),
            )

        # Current behavior: commands are never pruned (Phase 4 adds removal).
        self.fx.remove_command("cmd.md")
        self.assertEqual(0, self.fx.run().returncode)
        for agent in harness.COMMAND_DIRS:
            self.assertTrue((self.fx.commands_dir(agent) / "cmd.md").is_file())


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


if __name__ == "__main__":
    unittest.main()
