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
  * Only paths from the previous manifest, inside the selected scope, are
    pruned.
  * Global rules files receive a marked repository-owned block; all content
    outside the block is preserved. An existing rules file without the block
    is left intact and the block is appended.

Every run is planned before it mutates anything. ``--dry-run`` prints the plan
(creates, updates, conflicts, removals, unchanged). A real run writes each
changed file atomically, keeps a timestamped backup under
``~/.ai-rules/backups/``, and rolls the whole run back if any mutation fails.

Deployment targets all supported agents by default. ``--agent <name>`` (repeat
the option for more than one) narrows the run to the named agents and leaves
every other agent's installed content untouched.

Usage:
    python3 sync_ai_rules.py                 # pull latest and distribute to all
    python3 sync_ai_rules.py --dry-run       # print the plan, change nothing
    python3 sync_ai_rules.py --agent claude  # only Claude Code
    python3 sync_ai_rules.py --force         # overwrite locally modified files
    python3 sync_ai_rules.py --uninstall     # remove all managed content
    python3 sync_ai_rules.py --restore       # restore the most recent backup
    python3 sync_ai_rules.py --check         # report revision and content drift

``--check`` reports the repository-update status (installed revision vs fetched
upstream) and the installation-integrity status separately. Integrity compares
every managed path against its recorded SHA-256 and lists modified, missing,
unexpected, and obsolete artifacts. It exits nonzero for content drift or when the
required integrity check (the manifest) cannot be evaluated; repository currency
is informational.

Network access is required to clone/pull. Offline runs reuse the local copy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO_URL = "https://github.com/doberkofler/awesome-ai-prompts.git"
CACHE_DIR = Path.home() / ".ai-rules" / "src"
MANIFEST_FILE = Path.home() / ".ai-rules" / "manifest.json"
BACKUP_DIR = Path.home() / ".ai-rules" / "backups"
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

# Which shared skills directory each agent reads.
AGENT_SKILL_TARGETS = {
    "opencode": HOME / ".agents" / "skills",
    "codex": HOME / ".agents" / "skills",
    "pi": HOME / ".agents" / "skills",
    "claude": HOME / ".claude" / "skills",
}

# Legacy directories earlier versions of this installer created. Each is gated
# by the agent it belonged to. OpenCode's native skills directory is user-owned
# and is never removed.
OBSOLETE_DIRS = (
    ("pi", HOME / ".pi" / "agent" / "skills"),
    ("opencode", HOME / ".config" / "opencode" / "docs"),
    ("claude", HOME / ".claude" / "rules"),
)

CODEX_DEFAULT_MAX_BYTES = 32768
CODEX_RECOMMENDED_MAX_BYTES = 65536


# ---------------------------------------------------------------------------
# Repository resolution
# ---------------------------------------------------------------------------


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
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
    if not branch or branch == "HEAD":
        print(f"NOTE: {repo} is checked out at a fixed revision; skipping git pull.")
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
    # --check / --uninstall / --restore: clone if needed, never pull.
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


def is_under(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def selected_agents(requested: list[str] | None) -> tuple[str, ...]:
    if not requested:
        return ALL_AGENTS
    selected: list[str] = []
    for name in requested:
        if name not in ALL_AGENTS:
            sys.exit(
                f"unknown agent: {name}\n"
                f"choose from: {', '.join(ALL_AGENTS)}"
            )
        if name not in selected:
            selected.append(name)
    return tuple(selected)


def selected_skill_targets(agents: tuple[str, ...]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(AGENT_SKILL_TARGETS[agent] for agent in agents))


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

    for dest in set(AGENT_SKILL_TARGETS.values()):
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
    text = manifest.to_json()
    if MANIFEST_FILE.is_file() and MANIFEST_FILE.read_text(encoding="utf-8") == text:
        return
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(MANIFEST_FILE, text.encode("utf-8"))


def remove_legacy_state() -> None:
    for legacy in (LEGACY_STATE_FILE, LEGACY_MANAGED_SKILLS_FILE):
        if legacy.is_file():
            legacy.unlink()


# ---------------------------------------------------------------------------
# Plan model: what a run intends to do, computed before any mutation
# ---------------------------------------------------------------------------


@dataclass
class Action:
    op: str  # create | update | remove
    kind: str  # rules | command | skill | obsolete
    relative: str
    data: bytes | None = None
    note: str = ""

    @property
    def target(self) -> Path:
        return abs_from_home(self.relative)


@dataclass
class Conflict:
    kind: str
    relative: str
    reason: str  # unmanaged | modified | malformed

    def message(self) -> str:
        path = abs_from_home(self.relative)
        if self.reason == "unmanaged":
            return (
                f"refusing to replace unmanaged {self.kind}: {path}\n"
                "It is not recorded as managed by this repository.\n"
                "Move or remove it, then run again."
            )
        if self.reason == "modified":
            return (
                f"refusing to replace locally modified {self.kind}: {path}\n"
                "Re-run with --force to overwrite your changes."
            )
        return f"cannot install {self.kind}: {path}\n{self.reason}"


@dataclass
class Plan:
    actions: list[Action] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    unchanged: list[tuple[str, str]] = field(default_factory=list)
    kept: list[tuple[str, str]] = field(default_factory=list)
    managed_files: list[tuple[str, str, str]] = field(default_factory=list)
    cleared_roots: list[str] = field(default_factory=list)
    block_hashes: dict[str, str] = field(default_factory=dict)
    skill_count: int = 0
    skill_files: int = 0


def merge_plans(plans: list[Plan]) -> Plan:
    merged = Plan()
    for plan in plans:
        merged.actions.extend(plan.actions)
        merged.conflicts.extend(plan.conflicts)
        merged.unchanged.extend(plan.unchanged)
        merged.kept.extend(plan.kept)
        merged.managed_files.extend(plan.managed_files)
        merged.cleared_roots.extend(plan.cleared_roots)
        merged.block_hashes.update(plan.block_hashes)
        merged.skill_count += plan.skill_count
        merged.skill_files += plan.skill_files
    return merged


# ---------------------------------------------------------------------------
# Planners
# ---------------------------------------------------------------------------


def plan_file_set(
    desired: dict[str, bytes],
    manifest: Manifest,
    kind: str,
    force: bool,
    roots: tuple[Path, ...],
) -> Plan:
    """Plan per-file creates, updates, conflicts, and managed prunes."""
    plan = Plan()
    plan.cleared_roots = [rel_to_home(root) for root in roots]

    for relative in sorted(desired):
        target = abs_from_home(relative)
        entry = manifest.files.get(relative)
        if target.is_file():
            if entry is None:
                plan.conflicts.append(Conflict(kind, relative, "unmanaged"))
            elif sha256_file(target) != entry["sha256"]:
                if force:
                    plan.actions.append(
                        Action(
                            "update",
                            kind,
                            relative,
                            desired[relative],
                            "overwrite local changes",
                        )
                    )
                else:
                    plan.conflicts.append(Conflict(kind, relative, "modified"))
            elif target.read_bytes() != desired[relative]:
                plan.actions.append(Action("update", kind, relative, desired[relative]))
            else:
                plan.unchanged.append((kind, relative))
        elif target.exists():
            # A directory occupies a path where a file belongs.
            plan.conflicts.append(Conflict(kind, relative, "unmanaged"))
        else:
            plan.actions.append(Action("create", kind, relative, desired[relative]))

    for relative in sorted(manifest.files):
        entry = manifest.files[relative]
        if entry.get("kind") != kind:
            continue
        if not any(is_under(abs_from_home(relative), root) for root in roots):
            continue
        if relative in desired:
            continue
        target = abs_from_home(relative)
        if not target.is_file():
            plan.unchanged.append((kind, relative))
        elif sha256_file(target) == entry["sha256"]:
            plan.actions.append(Action("remove", kind, relative, None, "obsolete"))
        else:
            plan.kept.append((kind, relative))

    for relative, data in desired.items():
        plan.managed_files.append((relative, kind, sha256_bytes(data)))
    return plan


def plan_commands(
    repo: Path, manifest: Manifest, agents: tuple[str, ...], force: bool
) -> Plan:
    desired: dict[str, bytes] = {}
    for agent in agents:
        directory = TARGETS[agent]["commands"]
        for source in command_files(repo):
            desired[rel_to_home(directory / source.name)] = source.read_bytes()
    roots = tuple(TARGETS[agent]["commands"] for agent in agents)
    return plan_file_set(desired, manifest, "command", force, roots)


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


def plan_skills(
    repo: Path, manifest: Manifest, targets: tuple[Path, ...], force: bool
) -> Plan:
    skills = skill_dirs(repo)
    payloads = {skill.name: skill_payload(skill) for skill in skills}
    desired: dict[str, bytes] = {}
    for dest in targets:
        for skill in skills:
            for relative, data in payloads[skill.name].items():
                desired[rel_to_home(dest / skill.name / relative)] = data
    plan = plan_file_set(desired, manifest, "skill", force, targets)
    plan.skill_count = len(skills)
    plan.skill_files = sum(len(files) for files in payloads.values())
    return plan


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


def remove_block(text: str) -> str:
    start = text.index(BLOCK_BEGIN)
    end = text.index(BLOCK_END) + len(BLOCK_END)
    before = text[:start].rstrip("\n")
    after = text[end:].lstrip("\n")
    if before and after:
        return before + "\n\n" + after
    if before:
        return before + "\n"
    return after


def _rules_change(
    plan: Plan, key: str, existing: str, new_text: str, note: str
) -> None:
    if not new_text.endswith("\n"):
        new_text += "\n"
    if new_text == existing:
        plan.unchanged.append(("rules", key))
    else:
        plan.actions.append(
            Action("update", "rules", key, new_text.encode("utf-8"), note)
        )


def plan_rules(
    repo: Path, manifest: Manifest, agents: tuple[str, ...], force: bool
) -> Plan:
    body = rules_body(repo)
    block = render_block(body)
    body_hash = sha256_bytes(body.encode("utf-8"))
    plan = Plan()

    for agent in agents:
        dest = TARGETS[agent]["rules"]
        key = rel_to_home(dest)

        if not dest.exists():
            plan.actions.append(
                Action("create", "rules", key, block.encode("utf-8"), "managed block")
            )
        else:
            existing = dest.read_text(encoding="utf-8")
            if has_block(existing):
                previous_hash = manifest.blocks.get(key, {}).get("sha256", "")
                current_hash = sha256_bytes(block_body(existing).encode("utf-8"))
                if previous_hash and previous_hash != current_hash and not force:
                    plan.conflicts.append(Conflict("rules block", key, "modified"))
                    continue
                _rules_change(plan, key, existing, replace_block(existing, block), "")
            elif existing.lstrip().startswith(LEGACY_MARKER_PREFIX):
                _rules_change(plan, key, existing, block, "migrate legacy file")
            elif BLOCK_BEGIN in existing or BLOCK_END in existing:
                plan.conflicts.append(
                    Conflict(
                        "rules block",
                        key,
                        "malformed block: expected exactly one BEGIN and one END marker",
                    )
                )
                continue
            elif not existing.strip():
                _rules_change(plan, key, existing, block, "")
            else:
                _rules_change(
                    plan,
                    key,
                    existing,
                    existing.rstrip("\n") + "\n\n" + block,
                    "append; existing content preserved",
                )

        plan.block_hashes[key] = body_hash

    return plan


def plan_obsolete(repo: Path, agents: tuple[str, ...]) -> Plan:
    """Plan removal of legacy directories created by older installer versions."""
    plan = Plan()
    managed_docs = {path.name for path in doc_files(repo)}
    for agent, directory in OBSOLETE_DIRS:
        if agent not in agents or not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                if directory.name in ("docs", "rules"):
                    if path.name not in managed_docs and path.name != ".DS_Store":
                        continue
                plan.actions.append(
                    Action("remove", "obsolete", rel_to_home(path), None, "legacy path")
                )
    return plan


# ---------------------------------------------------------------------------
# Executor: atomic writes, backup, and rollback
# ---------------------------------------------------------------------------


def ensure_parent(directory: Path, created: set[Path]) -> None:
    missing: list[Path] = []
    current = directory
    while not current.exists():
        missing.append(current)
        current = current.parent
    for path in reversed(missing):
        path.mkdir()
        created.add(path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def apply_action(action: Action, created: set[Path]) -> None:
    target = action.target
    if action.op == "remove":
        if target.is_file():
            target.unlink()
        return
    if action.data is None:
        raise ValueError(f"action {action.op} for {action.relative} has no data")
    ensure_parent(target.parent, created)
    atomic_write_bytes(target, action.data)


def capture_originals(actions: list[Action]) -> dict[str, bytes | None]:
    originals: dict[str, bytes | None] = {}
    for action in actions:
        target = action.target
        originals[action.relative] = target.read_bytes() if target.is_file() else None
    manifest_relative = rel_to_home(MANIFEST_FILE)
    originals.setdefault(
        manifest_relative,
        MANIFEST_FILE.read_bytes() if MANIFEST_FILE.is_file() else None,
    )
    return originals


def rollback(originals: dict[str, bytes | None], created: set[Path]) -> bool:
    ok = True
    for relative, data in originals.items():
        target = abs_from_home(relative)
        try:
            if data is None:
                if target.is_file():
                    target.unlink()
            else:
                ensure_parent(target.parent, set())
                atomic_write_bytes(target, data)
        except OSError:
            ok = False
    for directory in sorted(created, key=lambda p: len(p.parts), reverse=True):
        try:
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
        except OSError:
            ok = False
    return ok


def create_backup(actions: list[Action], label: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    base = f"{timestamp}-{os.getpid()}-{label}"
    name = base
    counter = 1
    while (BACKUP_DIR / name).exists():
        name = f"{base}-{counter}"
        counter += 1
    directory = BACKUP_DIR / name
    files_dir = directory / "files"
    entries: list[dict[str, object]] = []
    seen: set[str] = set()

    for action in actions:
        if action.relative in seen:
            continue
        seen.add(action.relative)
        target = action.target
        existed = target.is_file()
        entries.append(
            {
                "relative": action.relative,
                "kind": action.kind,
                "op": action.op,
                "existed": existed,
            }
        )
        if existed:
            dest = files_dir / action.relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dest)

    manifest_relative = rel_to_home(MANIFEST_FILE)
    manifest_existed = MANIFEST_FILE.is_file()
    entries.append(
        {
            "relative": manifest_relative,
            "kind": "manifest",
            "op": "update",
            "existed": manifest_existed,
        }
    )
    if manifest_existed:
        dest = files_dir / manifest_relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MANIFEST_FILE, dest)

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "backup.json").write_text(
        json.dumps(
            {"label": label, "timestamp": timestamp, "entries": entries},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return directory


def prune_empty_parents(removed: list[Path], roots: list[tuple[Path, bool]]) -> None:
    for path in removed:
        for root, allow_root in roots:
            if not is_under(path, root):
                continue
            current = path.parent
            while (
                current != root
                and is_under(current, root)
                and current.is_dir()
                and not any(current.iterdir())
            ):
                current.rmdir()
                print(f"cleanup -> removed {current}")
                current = current.parent
            if allow_root and root.is_dir() and not any(root.iterdir()):
                root.rmdir()
                print(f"cleanup -> removed {root}")
            break


def apply_run(
    actions: list[Action],
    label: str,
    prune_roots: list[tuple[Path, bool]],
    finalize,
) -> int:
    if not actions:
        finalize()
        return 0

    backup = create_backup(actions, label)
    originals = capture_originals(actions)
    created: set[Path] = set()
    try:
        for action in actions:
            apply_action(action, created)
        removed = [action.target for action in actions if action.op == "remove"]
        prune_empty_parents(removed, prune_roots)
        finalize()
    except OSError as error:
        restored = rollback(originals, created)
        if restored:
            shutil.rmtree(backup, ignore_errors=True)
        print(f"ERROR: {error}", file=sys.stderr)
        if restored:
            print(
                "the run failed and every change was rolled back.",
                file=sys.stderr,
            )
        else:
            print(
                f"the run failed. Rollback was incomplete; backup kept at {backup}",
                file=sys.stderr,
            )
        return 1
    return 0


# ---------------------------------------------------------------------------
# Plan and summary reporting
# ---------------------------------------------------------------------------


def print_plan(plan: Plan, dry_run: bool) -> None:
    print("dry run:" if dry_run else "plan:")
    for op, label in (("create", "create"), ("update", "update"), ("remove", "remove")):
        for action in plan.actions:
            if action.op != op:
                continue
            note = f"  ({action.note})" if action.note else ""
            print(f"  {label:<7} {action.kind:<9} {action.target}{note}")
    for conflict in plan.conflicts:
        print(
            f"  conflict {conflict.kind:<9} "
            f"{abs_from_home(conflict.relative)}  ({conflict.reason})"
        )
    for kind, relative in plan.kept:
        print(f"  kept     {kind:<9} {abs_from_home(relative)}  (locally modified)")
    if dry_run:
        for kind, relative in plan.unchanged:
            print(f"  unchanged {kind:<9} {abs_from_home(relative)}")
    if not plan.actions and not plan.conflicts and not plan.kept:
        print("  (nothing to do)")


def report_conflicts(plan: Plan) -> None:
    print(
        "installation blocked by conflicting targets:",
        file=sys.stderr,
    )
    for conflict in plan.conflicts:
        print(file=sys.stderr)
        print(conflict.message(), file=sys.stderr)


# ---------------------------------------------------------------------------
# Manifest application
# ---------------------------------------------------------------------------


def apply_manifest(manifest: Manifest, plan: Plan, repo: str) -> None:
    for root in plan.cleared_roots:
        root_path = abs_from_home(root)
        manifest.files = {
            key: value
            for key, value in manifest.files.items()
            if not is_under(abs_from_home(key), root_path)
        }
    for relative, kind, digest in plan.managed_files:
        manifest.files[relative] = {"sha256": digest, "kind": kind}
    for key, digest in plan.block_hashes.items():
        manifest.blocks[key] = {"sha256": digest}
    manifest.repo = repo


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    word = singular if count == 1 else (plural_form or singular + "s")
    return f"{count} {word}"


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


def warn_codex_size(body: str) -> None:
    path = TARGETS["codex"]["rules"]
    size = len(body.encode("utf-8"))
    limit = read_codex_max_bytes(TARGETS["codex"]["config"])
    if size >= limit:
        print()
        print(f"WARNING: {path} is {size} bytes but project_doc_max_bytes={limit}.")
        print("Codex will truncate instructions. Add this to ~/.codex/config.toml:")
        print(f"    project_doc_max_bytes = {CODEX_RECOMMENDED_MAX_BYTES}")


def warn_opencode_skill_overrides(repo: Path, agents: tuple[str, ...]) -> None:
    if "opencode" not in agents:
        return
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


def print_summary(
    plan: Plan,
    docs: int,
    skills: int,
    commands: int,
    agents: tuple[str, ...],
) -> None:
    print()
    print("summary")
    print(f"  agents    {', '.join(agents)}")
    print(f"  rules     {plural(docs, 'doc')} -> {len(agents)} locations")
    print(
        f"  skills    {plural(skills, 'skill')} ({plural(plan.skill_files, 'file')})"
        f" -> {len(selected_skill_targets(agents))} locations"
    )
    print(f"  commands  {plural(commands, 'command')} -> {len(agents)} locations")


def sync_prune_roots(
    agents: tuple[str, ...], skill_targets: tuple[Path, ...]
) -> list[tuple[Path, bool]]:
    roots = [(TARGETS[agent]["commands"], False) for agent in agents]
    roots.extend((target, False) for target in skill_targets)
    roots.extend(
        (directory, True) for agent, directory in OBSOLETE_DIRS if agent in agents
    )
    return roots


def do_sync(force: bool, agents: tuple[str, ...], dry_run: bool) -> int:
    repo = resolve_repo(pull=True)
    sha = git_short_sha(repo)
    print(f"source: {repo} @ {sha}\n")
    manifest = load_manifest(repo, sha)
    skill_targets = selected_skill_targets(agents)

    plan = merge_plans(
        [
            plan_rules(repo, manifest, agents, force),
            plan_commands(repo, manifest, agents, force),
            plan_skills(repo, manifest, skill_targets, force),
            plan_obsolete(repo, agents),
        ]
    )

    if dry_run:
        print_plan(plan, dry_run=True)
        return 0

    if plan.conflicts:
        report_conflicts(plan)
        return 1

    print_plan(plan, dry_run=False)

    def finalize() -> None:
        apply_manifest(manifest, plan, sha)
        save_manifest(manifest)
        remove_legacy_state()

    status = apply_run(
        plan.actions, "sync", sync_prune_roots(agents, skill_targets), finalize
    )
    if status != 0:
        return status

    if "codex" in agents:
        warn_codex_size(rules_body(repo))
    print_summary(
        plan,
        len(doc_files(repo)),
        len(skill_dirs(repo)),
        len(command_files(repo)),
        agents,
    )
    warn_opencode_skill_overrides(repo, agents)
    print(f"\nrecorded {sha} in {MANIFEST_FILE}")
    print("done.")
    return 0


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------


def plan_uninstall(
    repo: Path, manifest: Manifest, agents: tuple[str, ...], force: bool
) -> tuple[Plan, Manifest]:
    plan = Plan()
    command_roots = [TARGETS[agent]["commands"] for agent in agents]
    skill_roots = list(selected_skill_targets(agents))
    rule_keys = {rel_to_home(TARGETS[agent]["rules"]) for agent in agents}

    remaining_files: dict[str, dict[str, str]] = {}
    remaining_blocks: dict[str, dict[str, str]] = {}

    for relative, entry in sorted(manifest.files.items()):
        target = abs_from_home(relative)
        in_scope = any(is_under(target, root) for root in command_roots) or any(
            is_under(target, root) for root in skill_roots
        )
        if not in_scope:
            remaining_files[relative] = entry
            continue
        if not target.is_file():
            continue
        kind = entry.get("kind", "file")
        if sha256_file(target) == entry["sha256"]:
            plan.actions.append(Action("remove", kind, relative, None, "uninstall"))
        elif force:
            plan.actions.append(
                Action("remove", kind, relative, None, "uninstall (forced)")
            )
        else:
            plan.kept.append((kind, relative))
            remaining_files[relative] = entry

    for key, entry in sorted(manifest.blocks.items()):
        target = abs_from_home(key)
        if key not in rule_keys:
            remaining_blocks[key] = entry
            continue
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8")
        if not has_block(text):
            remaining_blocks[key] = entry
            continue
        current = sha256_bytes(block_body(text).encode("utf-8"))
        if entry.get("sha256") and entry["sha256"] != current and not force:
            plan.kept.append(("rules block", key))
            remaining_blocks[key] = entry
            continue
        new_text = remove_block(text)
        if not new_text.strip():
            plan.actions.append(Action("remove", "rules", key, None, "uninstall"))
        else:
            plan.actions.append(
                Action("update", "rules", key, new_text.encode("utf-8"), "uninstall block")
            )

    plan.actions.extend(plan_obsolete(repo, agents).actions)
    remaining = Manifest(
        repo=manifest.repo, files=remaining_files, blocks=remaining_blocks
    )
    return plan, remaining


def do_uninstall(agents: tuple[str, ...], force: bool, dry_run: bool) -> int:
    if (
        not MANIFEST_FILE.is_file()
        and not LEGACY_STATE_FILE.is_file()
        and not LEGACY_MANAGED_SKILLS_FILE.is_file()
    ):
        print("nothing to uninstall (no manifest found).")
        return 0

    repo = resolve_repo(pull=False)
    sha = git_short_sha(repo)
    manifest = load_manifest(repo, sha)
    plan, remaining = plan_uninstall(repo, manifest, agents, force)

    if dry_run:
        print_plan(plan, dry_run=True)
        return 0

    print_plan(plan, dry_run=False)
    skill_targets = selected_skill_targets(agents)

    def finalize() -> None:
        if remaining.files or remaining.blocks:
            save_manifest(remaining)
        elif MANIFEST_FILE.is_file():
            MANIFEST_FILE.unlink()
        remove_legacy_state()

    if remaining.files or remaining.blocks:
        print(
            "\nNOTE: locally modified content was kept and remains recorded "
            "in the manifest."
        )

    prune_roots = [(TARGETS[agent]["commands"], True) for agent in agents]
    prune_roots.extend((target, True) for target in skill_targets)
    prune_roots.extend(
        (directory, True) for agent, directory in OBSOLETE_DIRS if agent in agents
    )

    status = apply_run(plan.actions, "uninstall", prune_roots, finalize)
    if status != 0:
        return status
    print("\nuninstall complete.")
    return 0


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------


def do_restore(name: str) -> int:
    if name == "latest":
        if not BACKUP_DIR.is_dir():
            sys.exit("no backups found.")
        candidates = sorted(path for path in BACKUP_DIR.iterdir() if path.is_dir())
        if not candidates:
            sys.exit("no backups found.")
        directory = candidates[-1]
    else:
        directory = BACKUP_DIR / name
    if not directory.is_dir():
        sys.exit(f"backup not found: {directory}")

    try:
        data = json.loads((directory / "backup.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"cannot read backup {directory}: {error}")

    restored = 0
    for entry in data.get("entries", []):
        target = abs_from_home(str(entry["relative"]))
        if entry.get("existed"):
            source = directory / "files" / str(entry["relative"])
            atomic_write_bytes(target, source.read_bytes())
            restored += 1
        elif target.is_file():
            target.unlink()
            restored += 1

    print(f"restored {plural(restored, 'path')} from {directory}")
    return 0


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------


def print_inventory(repo: Path) -> None:
    print("inventory")
    print(f"  rules     {plural(len(doc_files(repo)), 'doc')}")
    print(f"  skills    {plural(len(skill_dirs(repo)), 'skill')}")
    print(f"  commands  {plural(len(command_files(repo)), 'command')}")


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


def desired_file_paths(repo: Path) -> set[str]:
    """Every file path the current source would install, for all agents."""
    paths: set[str] = set()
    for agent in ALL_AGENTS:
        directory = TARGETS[agent]["commands"]
        for source in command_files(repo):
            paths.add(rel_to_home(directory / source.name))
    for target in dict.fromkeys(AGENT_SKILL_TARGETS.values()):
        for skill in skill_dirs(repo):
            for relative in skill_payload(skill):
                paths.add(rel_to_home(target / skill.name / relative))
    return paths


def desired_block_hashes(repo: Path) -> dict[str, str]:
    """Every rules block the current source would install, for all agents."""
    body = rules_body(repo)
    digest = sha256_bytes(body.encode("utf-8"))
    return {rel_to_home(TARGETS[agent]["rules"]): digest for agent in ALL_AGENTS}


@dataclass
class IntegrityReport:
    """Per-artifact installation drift, grouped for separate reporting."""

    modified: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    obsolete: list[str] = field(default_factory=list)

    @property
    def drift(self) -> bool:
        return bool(self.modified or self.missing or self.unexpected or self.obsolete)


def try_load_manifest() -> Manifest | None:
    """Return the manifest, or ``None`` when absent or unreadable."""
    if not MANIFEST_FILE.is_file():
        return None
    try:
        return Manifest.from_json(MANIFEST_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return None


def check_integrity(repo: Path, manifest: Manifest) -> IntegrityReport:
    """Compare installed content against the manifest and the current source.

    Classification is relative to the manifest, so an agent that was never
    installed is not reported as missing:

    * ``modified``   a managed path exists but its content no longer matches
                     its recorded hash (including a rules block body);
    * ``missing``    a managed path is absent, or a recorded rules block no
                     longer has its markers;
    * ``unexpected`` the current source wants a path that exists but is not
                     recorded in the manifest (an unmanaged collision);
    * ``obsolete``   a recorded path that the current source no longer
                     distributes (it would be pruned by the next run).
    """
    report = IntegrityReport()
    desired_files = desired_file_paths(repo)
    desired_blocks = desired_block_hashes(repo)

    for relative, entry in sorted(manifest.files.items()):
        target = abs_from_home(relative)
        if not target.is_file():
            report.missing.append(relative)
        elif sha256_file(target) != entry["sha256"]:
            report.modified.append(relative)
        elif relative not in desired_files:
            report.obsolete.append(relative)

    for key, entry in sorted(manifest.blocks.items()):
        target = abs_from_home(key)
        if not target.is_file():
            report.missing.append(key)
            continue
        text = target.read_text(encoding="utf-8")
        if not has_block(text):
            report.missing.append(key)
            continue
        if sha256_bytes(block_body(text).encode("utf-8")) != entry["sha256"]:
            report.modified.append(key)

    for relative in sorted(desired_files):
        if relative in manifest.files:
            continue
        if abs_from_home(relative).is_file():
            report.unexpected.append(relative)

    for key in sorted(desired_blocks):
        if key in manifest.blocks:
            continue
        target = abs_from_home(key)
        if target.is_file() and has_block(target.read_text(encoding="utf-8")):
            report.unexpected.append(key)

    return report


def read_upstream_sha(repo: Path) -> str | None:
    """Fetch and resolve the upstream short SHA, or ``None`` when unavailable."""
    run_git(["fetch", "origin"], repo)
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
    if not branch or branch == "HEAD":
        return None
    result = run_git(["rev-parse", "--short", f"origin/{branch}"], repo)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def do_check() -> int:
    repo = resolve_repo(pull=False)
    installed = read_installed_revision()
    upstream_sha = read_upstream_sha(repo)

    print("repository")
    print(f"  installed  {installed}")
    print(f"  upstream   {upstream_sha or 'unavailable'}")
    if upstream_sha is None:
        repo_status = "unknown"
    elif installed == upstream_sha:
        repo_status = "up to date"
    else:
        repo_status = "update available"
    print(f"  status     {repo_status}")

    print()
    print("integrity")
    manifest = try_load_manifest()
    if manifest is not None:
        report = check_integrity(repo, manifest)
        for label in ("modified", "missing", "unexpected", "obsolete"):
            for relative in getattr(report, label):
                print(f"  {label:<10} {abs_from_home(relative)}")
        integrity_status = "drift detected" if report.drift else "ok"
        integrity_problem = report.drift
    elif LEGACY_STATE_FILE.is_file():
        integrity_status = "unknown (legacy install; run the installer to migrate)"
        integrity_problem = True
    else:
        integrity_status = "not installed"
        integrity_problem = True
    print(f"  status     {integrity_status}")

    print()
    print_inventory(repo)

    # Only installation integrity is a required check. Repository currency is
    # informational: a verified release archive has no git metadata to compare.
    return 1 if integrity_problem else 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Distribute local AI rules.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the installed revision with the upstream revision",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan without changing anything",
    )
    parser.add_argument(
        "--agent",
        action="append",
        dest="agents",
        metavar="AGENT",
        help=f"limit the run to an agent (repeatable): {', '.join(ALL_AGENTS)}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite locally modified managed files without prompting",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="remove all repository-managed content",
    )
    parser.add_argument(
        "--restore",
        nargs="?",
        const="latest",
        metavar="BACKUP",
        help="restore an installer-created backup (default: latest)",
    )
    args = parser.parse_args()

    if args.restore is not None:
        return do_restore(args.restore)
    if args.check:
        return do_check()

    agents = selected_agents(args.agents)
    if args.uninstall:
        return do_uninstall(agents, args.force, args.dry_run)
    return do_sync(args.force, agents, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
