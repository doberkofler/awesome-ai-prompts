#!/usr/bin/env python3
"""Distribute the canonical AI rules to the local agent configurations.

Canonical source: https://github.com/doberkofler/awesome-ai-prompts

The same content is written to each supported agent's user-level location:

  opencode    rules:    ~/.config/opencode/AGENTS.md       (managed block)
              commands: ~/.config/opencode/commands/*.md
              skills:   reads ~/.agents/skills/<name>/
  Claude Code rules:    ~/.claude/CLAUDE.md                 (managed block)
              commands: ~/.claude/commands/*.md
              skills:   ~/.claude/skills/<name>/
  Codex       rules:    ~/.codex/AGENTS.md                  (managed block)
              commands: ~/.codex/prompts/*.md               (deprecated by Codex)
              skills:   reads ~/.agents/skills/<name>/
  Pi          rules:    ~/.pi/agent/AGENTS.md               (managed block)
              commands: ~/.pi/agent/prompts/*.md
              skills:   reads ~/.agents/skills/<name>/

Skills are written to only two locations, because each harness scans several
directories at once and duplicate skill names across them collide:

  ~/.agents/skills   read by opencode, Codex, and Pi
  ~/.claude/skills   read by Claude Code

Everything else is per-harness; there is no cross-agent standard for rules or
commands.

Ownership model:

  * Every distributed file is recorded with its SHA-256 in
    ``~/.ai-rules/manifest.json``.
  * A path that exists but is not recorded is user-owned and is never
    overwritten.
  * A recorded path whose content no longer matches its hash is locally
    modified and is never overwritten unless ``--force`` is given.
  * Only paths from the previous manifest are pruned.
  * Global rules files receive a marked repository-owned block; all content
    outside the block is preserved. An existing rules file without the block
    is left intact and the block is appended.

Usage:
    python3 sync_ai_rules.py            # pull latest and distribute
    python3 sync_ai_rules.py --check    # report whether the install is current
    python3 sync_ai_rules.py --force    # overwrite locally modified managed files

Network access is required to clone/pull. Offline runs reuse the local copy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_URL = "https://github.com/doberkofler/awesome-ai-prompts.git"
CACHE_DIR = Path.home() / ".ai-rules" / "src"
MANIFEST_FILE = Path.home() / ".ai-rules" / "manifest.json"
LEGACY_STATE_FILE = Path.home() / ".ai-rules" / "installed"
LEGACY_MANAGED_SKILLS_FILE = Path.home() / ".ai-rules" / "managed-skills"
# Backwards-compatible alias used by older callers and checks.
STATE_FILE = LEGACY_STATE_FILE

MANIFEST_VERSION = 1
BLOCK_BEGIN = "<!-- BEGIN awesome-ai-prompts (managed) -->"
BLOCK_END = "<!-- END awesome-ai-prompts -->"
LEGACY_MARKER_PREFIX = "<!-- awesome-ai-prompts "

HOME = Path.home()
TARGETS = {
    "opencode": {
        "rules": HOME / ".config" / "opencode" / "AGENTS.md",
        "commands": HOME / ".config" / "opencode" / "commands",
        "skills": HOME / ".agents" / "skills",
    },
    "claude": {
        "rules": HOME / ".claude" / "CLAUDE.md",
        "commands": HOME / ".claude" / "commands",
        "skills": HOME / ".claude" / "skills",
    },
    "codex": {
        "rules": HOME / ".codex" / "AGENTS.md",
        "commands": HOME / ".codex" / "prompts",
        "skills": HOME / ".agents" / "skills",
        "config": HOME / ".codex" / "config.toml",
    },
    "pi": {
        "rules": HOME / ".pi" / "agent" / "AGENTS.md",
        "commands": HOME / ".pi" / "agent" / "prompts",
        "skills": HOME / ".agents" / "skills",
    },
}

ALL_AGENTS = ("opencode", "claude", "codex", "pi")

# The only two skills directories to write, and the legacy Pi directory this
# script created before skills were consolidated. Obsolete dirs are removed on
# sync. OpenCode's native skills directory is user-owned and must be preserved.
SKILL_TARGETS = (
    HOME / ".agents" / "skills",
    HOME / ".claude" / "skills",
)
OBSOLETE_SKILL_DIRS = (
    HOME / ".pi" / "agent" / "skills",
)
OBSOLETE_RULE_DIRS = (
    HOME / ".config" / "opencode" / "docs",
    HOME / ".claude" / "rules",
)

CODEX_DEFAULT_MAX_BYTES = 32768
CODEX_RECOMMENDED_MAX_BYTES = 65536


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )


def script_dir() -> Path | None:
    try:
        script = __file__
    except NameError:  # executed via `python3 -` (stdin)
        return None
    if script.startswith("<") and script.endswith(">"):
        return None
    return Path(script).resolve().parent


def git_short_sha(repo: Path) -> str:
    result = run_git(["rev-parse", "--short", "HEAD"], repo)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def pull_repo(repo: Path) -> None:
    if not (repo / ".git").is_dir():
        return
    status = run_git(["status", "--porcelain"], repo)
    if status.returncode != 0 or status.stdout.strip():
        print(f"NOTE: {repo} has local changes; skipping git pull.")
        return
    result = run_git(["pull", "--ff-only"], repo)
    if result.returncode != 0:
        print("WARNING: git pull failed (offline?); using the local copy.")
    else:
        text = (result.stdout or result.stderr).strip()
        if text:
            print(text)


def clone_cache() -> Path:
    if (CACHE_DIR / ".git").is_dir():
        pull_repo(CACHE_DIR)
        return CACHE_DIR
    if CACHE_DIR.exists():
        sys.exit(
            f"{CACHE_DIR} exists but is not a git repository.\n"
            "Remove it and run again."
        )
    CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
    result = run_git(["clone", REPO_URL, str(CACHE_DIR)], CACHE_DIR.parent)
    if result.returncode != 0:
        sys.exit("git clone failed:\n" + (result.stderr or "").strip())
    print((result.stderr or "").strip())
    return CACHE_DIR


def resolve_repo(pull: bool) -> Path:
    here = script_dir()
    if here is not None and (here / "docs").is_dir():
        if pull:
            pull_repo(here)
        return here
    if pull:
        return clone_cache()
    # --check: clone if needed, but never pull over the working copy
    if (CACHE_DIR / ".git").is_dir():
        return CACHE_DIR
    return clone_cache()


def doc_files(repo: Path) -> list[Path]:
    docs = repo / "docs"
    if not docs.is_dir():
        sys.exit(f"no docs/ directory in {repo}")
    return sorted(p for p in docs.glob("*.md") if p.is_file())


def skill_dirs(repo: Path) -> list[Path]:
    src = repo / "skills"
    if not src.is_dir():
        return []
    return [
        d for d in sorted(src.iterdir()) if d.is_dir() and not d.name.startswith(".")
    ]


def command_files(repo: Path) -> list[Path]:
    src = repo / "commands"
    if not src.is_dir():
        return []
    return sorted(p for p in src.glob("*.md") if p.is_file())


# ---------------------------------------------------------------------------
# Content hashing and HOME-relative path helpers
# ---------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel_to_home(path: Path) -> str:
    return path.relative_to(HOME).as_posix()


def abs_from_home(relative: str) -> Path:
    return HOME / Path(relative)


# ---------------------------------------------------------------------------
# Manifest: the single source of truth for repository-managed paths
# ---------------------------------------------------------------------------


@dataclass
class Manifest:
    """Repository-managed files and rule blocks, keyed by HOME-relative path."""

    repo: str = ""
    version: int = MANIFEST_VERSION
    files: dict[str, dict[str, str]] = field(default_factory=dict)
    blocks: dict[str, dict[str, str]] = field(default_factory=dict)

    def to_json(self) -> str:
        payload = {
            "version": self.version,
            "repo": self.repo,
            "files": {key: self.files[key] for key in sorted(self.files)},
            "blocks": {key: self.blocks[key] for key in sorted(self.blocks)},
        }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "Manifest":
        data = json.loads(text)
        if data.get("version") != MANIFEST_VERSION:
            raise ValueError(f"unsupported manifest version: {data.get('version')!r}")
        files = data.get("files", {})
        blocks = data.get("blocks", {})
        for key, value in files.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise ValueError(f"malformed file entry: {key!r}")
            if not isinstance(value.get("sha256"), str) or not value["sha256"]:
                raise ValueError(f"file entry has no hash: {key!r}")
        for key, value in blocks.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise ValueError(f"malformed block entry: {key!r}")
        return cls(
            repo=str(data.get("repo", "")),
            version=MANIFEST_VERSION,
            files=dict(files),
            blocks=dict(blocks),
        )


def read_legacy_managed_skill_names() -> set[str]:
    if LEGACY_MANAGED_SKILLS_FILE.is_file():
        return {
            line.strip()
            for line in LEGACY_MANAGED_SKILLS_FILE.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        }
    return set()


def migrate_legacy_manifest(repo: Path, sha: str) -> Manifest:
    """Adopt the paths an earlier installer version managed.

    The old layout tracked skills in ``managed-skills`` and left rules and
    commands untracked. There is no historical hash for those paths, so the
    current on-disk content becomes the baseline: it is treated as clean and is
    refreshed on this run.
    """
    manifest = Manifest(repo=sha)
    if not (LEGACY_STATE_FILE.is_file() or LEGACY_MANAGED_SKILLS_FILE.is_file()):
        return manifest

    for agent in ALL_AGENTS:
        dest = TARGETS[agent]["rules"]
        if dest.is_file():
            first_line = dest.read_text(encoding="utf-8").splitlines()[:1]
            if first_line and first_line[0].startswith(LEGACY_MARKER_PREFIX):
                manifest.blocks[rel_to_home(dest)] = {"sha256": ""}

    for dest in SKILL_TARGETS:
        for name in read_legacy_managed_skill_names():
            directory = dest / name
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    manifest.files[rel_to_home(path)] = {
                        "sha256": sha256_file(path),
                        "kind": "skill",
                    }

    source_commands = {path.name for path in command_files(repo)}
    for agent in ALL_AGENTS:
        directory = TARGETS[agent]["commands"]
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.name in source_commands:
                manifest.files[rel_to_home(path)] = {
                    "sha256": sha256_file(path),
                    "kind": "command",
                }

    print("NOTE: migrated legacy install state into the new manifest.")
    return manifest


def load_manifest(repo: Path, sha: str) -> Manifest:
    if MANIFEST_FILE.is_file():
        try:
            return Manifest.from_json(MANIFEST_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError) as error:
            sys.exit(
                f"cannot read {MANIFEST_FILE}: {error}\nRemove it and run again."
            )
    return migrate_legacy_manifest(repo, sha)


def save_manifest(manifest: Manifest) -> None:
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(manifest.to_json(), encoding="utf-8")


# ---------------------------------------------------------------------------
# Ownership classification and refusal helpers
# ---------------------------------------------------------------------------


def classify(relative: str, manifest: Manifest) -> str:
    """Return the ownership state of a HOME-relative path.

    One of ``absent``, ``managed``, ``modified``, ``missing``, or ``unmanaged``.
    """
    entry = manifest.files.get(relative)
    target = abs_from_home(relative)
    if not target.is_file():
        return "missing" if entry is not None else "absent"
    if entry is None:
        return "unmanaged"
    return "managed" if sha256_file(target) == entry["sha256"] else "modified"


def refuse_unmanaged(path: Path, kind: str) -> None:
    sys.exit(
        f"refusing to replace unmanaged {kind}: {path}\n"
        "It is not recorded as managed by this repository.\n"
        "Move or remove it, then run again."
    )


def refuse_modified(path: Path, kind: str) -> None:
    sys.exit(
        f"refusing to replace locally modified {kind}: {path}\n"
        "Re-run with --force to overwrite your changes."
    )


def preflight_files(
    desired: dict[str, bytes], manifest: Manifest, kind: str, force: bool
) -> None:
    """Refuse the whole run before mutating anything if any target conflicts."""
    for relative in sorted(desired):
        target = abs_from_home(relative)
        state = classify(relative, manifest)
        if state == "unmanaged":
            refuse_unmanaged(target, kind)
        if state == "modified" and not force:
            refuse_modified(target, kind)


# ---------------------------------------------------------------------------
# Rules: a marked managed block inside each agent's global rules file
# ---------------------------------------------------------------------------


def rules_body(repo: Path) -> str:
    sections = [
        path.read_text(encoding="utf-8").rstrip("\n") for path in doc_files(repo)
    ]
    return "\n\n".join(sections)


def render_block(body: str) -> str:
    return f"{BLOCK_BEGIN}\n{body}\n{BLOCK_END}\n"


def has_block(text: str) -> bool:
    return text.count(BLOCK_BEGIN) == 1 and text.count(BLOCK_END) == 1


def block_body(text: str) -> str:
    start = text.index(BLOCK_BEGIN) + len(BLOCK_BEGIN)
    end = text.index(BLOCK_END)
    return text[start:end].strip("\n")


def replace_block(text: str, block: str) -> str:
    start = text.index(BLOCK_BEGIN)
    end = text.index(BLOCK_END) + len(BLOCK_END)
    return text[:start] + block.rstrip("\n") + text[end:]


def distribute_rules(repo: Path, manifest: Manifest, force: bool) -> str:
    body = rules_body(repo)
    block = render_block(body)
    body_hash = sha256_bytes(body.encode("utf-8"))

    for agent in ALL_AGENTS:
        dest = TARGETS[agent]["rules"]
        key = rel_to_home(dest)

        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(block, encoding="utf-8")
            print(f"rules  -> {dest} (created)")
        else:
            existing = dest.read_text(encoding="utf-8")
            if has_block(existing):
                previous_hash = manifest.blocks.get(key, {}).get("sha256", "")
                current_hash = sha256_bytes(block_body(existing).encode("utf-8"))
                if previous_hash and previous_hash != current_hash and not force:
                    refuse_modified(dest, "rules block")
                new_text = replace_block(existing, block)
                print(f"rules  -> {dest} (updated)")
            elif existing.lstrip().startswith(LEGACY_MARKER_PREFIX):
                new_text = block
                print(f"rules  -> {dest} (migrated legacy file)")
            elif BLOCK_BEGIN in existing or BLOCK_END in existing:
                sys.exit(
                    f"malformed managed block in {dest}: expected exactly one "
                    f"{BLOCK_BEGIN!r} and one {BLOCK_END!r} marker."
                )
            elif not existing.strip():
                new_text = block
                print(f"rules  -> {dest} (created)")
            else:
                new_text = existing.rstrip("\n") + "\n\n" + block
                print(f"rules  -> {dest} (appended; existing content preserved)")
            if not new_text.endswith("\n"):
                new_text += "\n"
            dest.write_text(new_text, encoding="utf-8")

        manifest.blocks[key] = {"sha256": body_hash}

    return body


# ---------------------------------------------------------------------------
# Skills: per-file, sidecar exclusion limited to <skill-root>/agents/
# ---------------------------------------------------------------------------


def skill_payload(skill: Path) -> dict[str, bytes]:
    """Return the distributable files of a skill, keyed by relative path.

    Only a top-level ``agents/`` directory and ``.DS_Store`` files are omitted;
    a nested ``agents/`` directory is legitimate content.
    """
    payload: dict[str, bytes] = {}
    for path in sorted(skill.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(skill)
        if relative.parts and relative.parts[0] == "agents":
            continue
        if path.name == ".DS_Store":
            continue
        payload[relative.as_posix()] = path.read_bytes()
    return payload


def prune_empty_skill_dirs(dest: Path) -> None:
    for child in sorted(dest.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if child.is_dir() and not any(child.iterdir()):
            child.rmdir()
            print(f"cleanup -> removed {child}")


def distribute_skills(
    repo: Path, manifest: Manifest, force: bool
) -> tuple[int, int]:
    skills = skill_dirs(repo)
    payloads = {skill.name: skill_payload(skill) for skill in skills}
    total_files = sum(len(files) for files in payloads.values())

    desired: dict[str, bytes] = {}
    for dest in SKILL_TARGETS:
        for skill in skills:
            for relative, data in payloads[skill.name].items():
                desired[rel_to_home(dest / skill.name / relative)] = data

    preflight_files(desired, manifest, "skill", force)

    # Prune only files this repository previously wrote and no longer produces.
    for relative in sorted(manifest.files):
        entry = manifest.files[relative]
        if entry.get("kind") != "skill" or relative in desired:
            continue
        target = abs_from_home(relative)
        if not target.is_file():
            continue
        if sha256_file(target) == entry["sha256"]:
            target.unlink()
            print(f"remove -> {target}")
        else:
            print(f"NOTE: keeping locally modified managed skill file: {target}")

    for relative, data in sorted(desired.items()):
        target = abs_from_home(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    for dest in SKILL_TARGETS:
        for skill in skills:
            (dest / skill.name).mkdir(parents=True, exist_ok=True)
        prune_empty_skill_dirs(dest)

    manifest.files = {
        key: value
        for key, value in manifest.files.items()
        if value.get("kind") != "skill"
    }
    for relative, data in desired.items():
        manifest.files[relative] = {
            "sha256": sha256_bytes(data),
            "kind": "skill",
        }

    for dest in SKILL_TARGETS:
        print(f"skills -> {dest} ({len(skills)} skills)")
    return len(skills), total_files


# ---------------------------------------------------------------------------
# Commands: per-file ownership and pruning of obsolete managed commands
# ---------------------------------------------------------------------------


def desired_command_files(repo: Path) -> dict[str, bytes]:
    desired: dict[str, bytes] = {}
    sources = command_files(repo)
    for agent in ALL_AGENTS:
        directory = TARGETS[agent]["commands"]
        for source in sources:
            desired[rel_to_home(directory / source.name)] = source.read_bytes()
    return desired


def distribute_commands(repo: Path, manifest: Manifest, force: bool) -> int:
    desired = desired_command_files(repo)
    preflight_files(desired, manifest, "command", force)

    for relative in sorted(manifest.files):
        entry = manifest.files[relative]
        if entry.get("kind") != "command" or relative in desired:
            continue
        target = abs_from_home(relative)
        if not target.is_file():
            continue
        if sha256_file(target) == entry["sha256"]:
            target.unlink()
            print(f"remove -> {target}")
        else:
            print(f"NOTE: keeping locally modified managed command: {target}")

    for relative, data in sorted(desired.items()):
        target = abs_from_home(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    manifest.files = {
        key: value
        for key, value in manifest.files.items()
        if value.get("kind") != "command"
    }
    for relative, data in desired.items():
        manifest.files[relative] = {
            "sha256": sha256_bytes(data),
            "kind": "command",
        }

    count = len(command_files(repo))
    for agent in ALL_AGENTS:
        print(f"cmds   -> {TARGETS[agent]['commands']} ({count} files)")
    return count


def warn_opencode_skill_overrides(repo: Path) -> None:
    native = HOME / ".config" / "opencode" / "skills"
    if not native.is_dir():
        return
    overlaps = [
        skill.name
        for skill in skill_dirs(repo)
        if (native / skill.name).exists() or (native / f"{skill.name}.md").is_file()
    ]
    if not overlaps:
        return
    print(
        "\nNOTE: native OpenCode skills override matching synced skills from "
        "~/.agents/skills/:"
    )
    for name in overlaps:
        print(f"    {name}")


def remove_managed_docs(directory: Path, managed: set[str]) -> bool:
    leftovers = []
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and (entry.name in managed or entry.name == ".DS_Store"):
            entry.unlink()
        else:
            leftovers.append(entry)
    if not any(directory.iterdir()):
        directory.rmdir()
        print(f"cleanup -> removed {directory}")
        return True
    if leftovers:
        kept = ", ".join(sorted(p.name for p in leftovers))
        print(f"NOTE: {directory} kept (unmanaged entries remain): {kept}")
    return False


def cleanup_obsolete(repo: Path) -> int:
    removed = 0
    for directory in OBSOLETE_SKILL_DIRS:
        if directory.is_dir():
            shutil.rmtree(directory)
            print(f"cleanup -> removed {directory}")
            removed += 1
    managed = {p.name for p in doc_files(repo)}
    for directory in OBSOLETE_RULE_DIRS:
        if directory.is_dir() and remove_managed_docs(directory, managed):
            removed += 1
    return removed


def read_codex_max_bytes(config: Path) -> int:
    if not config.is_file():
        return CODEX_DEFAULT_MAX_BYTES
    for line in config.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("project_doc_max_bytes"):
            _, _, value = line.partition("=")
            try:
                return int(value.strip())
            except ValueError:
                return CODEX_DEFAULT_MAX_BYTES
    return CODEX_DEFAULT_MAX_BYTES


def warn_codex_size(combined: str) -> None:
    path = TARGETS["codex"]["rules"]
    size = len(combined.encode("utf-8"))
    limit = read_codex_max_bytes(TARGETS["codex"]["config"])
    if size >= limit:
        print()
        print(f"WARNING: {path} is {size} bytes but project_doc_max_bytes={limit}.")
        print("Codex will truncate instructions. Add this to ~/.codex/config.toml:")
        print(f"    project_doc_max_bytes = {CODEX_RECOMMENDED_MAX_BYTES}")


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    word = singular if count == 1 else (plural_form or singular + "s")
    return f"{count} {word}"


def print_inventory(repo: Path) -> None:
    skills = skill_dirs(repo)
    docs = doc_files(repo)
    commands = command_files(repo)
    print("inventory")
    print(f"  rules     {plural(len(docs), 'doc')}")
    print(f"  skills    {plural(len(skills), 'skill')}")
    print(f"  commands  {plural(len(commands), 'command')}")


def print_summary(
    docs: int,
    skills: int,
    skill_files: int,
    commands: int,
    cleanup: int,
) -> None:
    print()
    print("summary")
    print(f"  rules     {plural(docs, 'doc')} -> {len(ALL_AGENTS)} locations")
    print(
        f"  skills    {plural(skills, 'skill')} ({plural(skill_files, 'file')}) -> "
        f"{len(SKILL_TARGETS)} locations"
    )
    print(f"  commands  {plural(commands, 'command')} -> {len(ALL_AGENTS)} locations")
    print(f"  cleanup   {plural(cleanup, 'path')} removed")


def do_sync(force: bool) -> int:
    repo = resolve_repo(pull=True)
    sha = git_short_sha(repo)
    print(f"source: {repo} @ {sha}\n")
    manifest = load_manifest(repo, sha)
    combined = distribute_rules(repo, manifest, force)
    skills, skill_files = distribute_skills(repo, manifest, force)
    commands = distribute_commands(repo, manifest, force)
    cleanup = cleanup_obsolete(repo)
    warn_codex_size(combined)
    manifest.repo = sha
    save_manifest(manifest)
    for legacy in (LEGACY_STATE_FILE, LEGACY_MANAGED_SKILLS_FILE):
        if legacy.is_file():
            legacy.unlink()
    print_summary(len(doc_files(repo)), skills, skill_files, commands, cleanup)
    warn_opencode_skill_overrides(repo)
    print(f"\nrecorded {sha} in {MANIFEST_FILE}")
    print("done.")
    return 0


def read_installed_revision() -> str:
    if MANIFEST_FILE.is_file():
        try:
            return Manifest.from_json(
                MANIFEST_FILE.read_text(encoding="utf-8")
            ).repo or "(none)"
        except (json.JSONDecodeError, ValueError):
            return "(invalid manifest)"
    if LEGACY_STATE_FILE.is_file():
        return LEGACY_STATE_FILE.read_text(encoding="utf-8").strip() or "(none)"
    return "(none)"


def do_check() -> int:
    repo = resolve_repo(pull=False)
    run_git(["fetch", "origin"], repo)

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
    upstream = run_git(["rev-parse", "--short", f"origin/{branch}"], repo)
    if upstream.returncode != 0:
        print("WARNING: could not resolve upstream (offline?); skipping check.")
        return 0
    upstream_sha = upstream.stdout.strip()

    installed = read_installed_revision()

    print(f"installed: {installed}")
    print(f"upstream:  {upstream_sha}")
    if installed == upstream_sha:
        print("status:    up to date")
    else:
        print("status:    OUT OF DATE - run: python3 ~/.ai-rules/src/sync_ai_rules.py")
    print()
    print_inventory(repo)
    return 0 if installed == upstream_sha else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Distribute local AI rules.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the installed revision with the upstream revision",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite locally modified managed files without prompting",
    )
    args = parser.parse_args()
    return do_check() if args.check else do_sync(args.force)


if __name__ == "__main__":
    sys.exit(main())
