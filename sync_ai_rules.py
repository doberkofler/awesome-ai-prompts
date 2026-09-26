#!/usr/bin/env python3
"""Distribute the canonical AI rules to the local agent configurations.

Canonical source: https://github.com/doberkofler/awesome-ai-prompts

The same content is written to each supported agent's user-level location:

  opencode    rules:    ~/.config/opencode/AGENTS.md       (concatenated)
              commands: ~/.config/opencode/commands/*.md
              skills:   reads ~/.agents/skills/<name>/
  Claude Code rules:    ~/.claude/CLAUDE.md                 (concatenated)
              commands: ~/.claude/commands/*.md
              skills:   ~/.claude/skills/<name>/
  Codex       rules:    ~/.codex/AGENTS.md                  (concatenated)
              commands: ~/.codex/prompts/*.md               (deprecated by Codex)
              skills:   ~/.agents/skills/<name>/
  Pi          rules:    ~/.pi/agent/AGENTS.md               (concatenated)
              commands: ~/.pi/agent/prompts/*.md
              skills:   reads ~/.agents/skills/<name>/

Skills are written to only two locations, because each harness scans several
directories at once and duplicate skill names across them collide:

  ~/.agents/skills   read by opencode, Codex, and Pi
  ~/.claude/skills   read by Claude Code

Everything else is per-harness; there is no cross-agent standard for rules or
commands.

Usage:
    python3 sync_ai_rules.py            # pull latest and distribute
    python3 sync_ai_rules.py --check    # report whether the install is current

Network access is required to clone/pull. Offline runs reuse the local copy.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/doberkofler/awesome-ai-prompts.git"
CACHE_DIR = Path.home() / ".ai-rules" / "src"
STATE_FILE = Path.home() / ".ai-rules" / "installed"

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

# The only two skills directories to write, and the legacy dirs this script
# created before they were consolidated. Obsolete dirs are removed on sync.
SKILL_TARGETS = (
    HOME / ".agents" / "skills",
    HOME / ".claude" / "skills",
)
OBSOLETE_SKILL_DIRS = (
    HOME / ".config" / "opencode" / "skills",
    HOME / ".pi" / "agent" / "skills",
)
OBSOLETE_RULE_DIRS = (
    HOME / ".config" / "opencode" / "docs",
    HOME / ".claude" / "rules",
)

CODEX_DEFAULT_MAX_BYTES = 32768
CODEX_RECOMMENDED_MAX_BYTES = 65536
OPENCODE_DOCS_INSTRUCTION = re.compile(
    r'"instructions"\s*:\s*\[[^\]]*"docs/\*\.md"'
)


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )


def script_dir() -> Path | None:
    try:
        return Path(__file__).resolve().parent
    except NameError:  # executed via `python3 -` (stdin)
        return None


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


def opencode_docs_instruction_configs(repo: Path) -> list[Path]:
    configs = (
        HOME / ".config" / "opencode" / "opencode.json",
        HOME / ".config" / "opencode" / "opencode.jsonc",
        repo / "opencode.json",
        repo / "opencode.jsonc",
    )
    matches = []
    for config in configs:
        try:
            text = config.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        if OPENCODE_DOCS_INSTRUCTION.search(text):
            matches.append(config)
    return matches


def warn_opencode_duplicate_rules(repo: Path) -> None:
    configs = opencode_docs_instruction_configs(repo)
    if not configs:
        return
    print(
        "\nNOTE: opencode combines ~/.config/opencode/AGENTS.md with matching "
        'files from "instructions". Remove docs/*.md from:'
    )
    for config in configs:
        print(f"    {config}")


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


def count_files(directory: Path) -> int:
    return sum(
        1
        for p in directory.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def distribute_rules(repo: Path, sha: str) -> str:
    docs = doc_files(repo)

    parts = [f"<!-- awesome-ai-prompts {sha} -->", ""]
    for f in docs:
        parts.append(f.read_text(encoding="utf-8").rstrip() + "\n")
    combined = "\n".join(parts)

    for agent in ALL_AGENTS:
        dest = TARGETS[agent]["rules"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(combined, encoding="utf-8")
        print(f"rules  -> {dest}")

    return combined


def distribute_skills(repo: Path) -> tuple[int, int]:
    skills = skill_dirs(repo)
    names = {s.name for s in skills}
    ignore = shutil.ignore_patterns(".DS_Store", "agents")
    total_files = sum(count_files(s) for s in skills)

    for dest in SKILL_TARGETS:
        dest.mkdir(parents=True, exist_ok=True)
        for child in sorted(dest.iterdir()):
            if child.is_dir() and child.name not in names:
                shutil.rmtree(child)
        for skill in skills:
            target = dest / skill.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill, target, ignore=ignore)
        print(f"skills -> {dest} ({len(skills)} skills)")

    return len(skills), total_files


def distribute_commands(repo: Path) -> int:
    files = command_files(repo)
    for agent in ALL_AGENTS:
        dest = TARGETS[agent]["commands"]
        dest.mkdir(parents=True, exist_ok=True)
        for f in files:
            copy_file(f, dest / f.name)
        print(f"cmds   -> {dest} ({len(files)} files)")
    return len(files)


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


def write_state(repo: Path) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(git_short_sha(repo) + "\n", encoding="utf-8")


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


def do_sync() -> int:
    repo = resolve_repo(pull=True)
    sha = git_short_sha(repo)
    print(f"source: {repo} @ {sha}\n")
    combined = distribute_rules(repo, sha)
    skills, skill_files = distribute_skills(repo)
    commands = distribute_commands(repo)
    cleanup = cleanup_obsolete(repo)
    warn_codex_size(combined)
    write_state(repo)
    print_summary(len(doc_files(repo)), skills, skill_files, commands, cleanup)
    warn_opencode_duplicate_rules(repo)
    print(f"\nrecorded {sha} in {STATE_FILE}")
    print("done.")
    return 0


def do_check() -> int:
    repo = resolve_repo(pull=False)
    run_git(["fetch", "origin"], repo)

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
    upstream = run_git(["rev-parse", "--short", f"origin/{branch}"], repo)
    if upstream.returncode != 0:
        print("WARNING: could not resolve upstream (offline?); skipping check.")
        return 0
    upstream_sha = upstream.stdout.strip()

    installed = "(none)"
    if STATE_FILE.is_file():
        installed = STATE_FILE.read_text(encoding="utf-8").strip() or "(none)"

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
    args = parser.parse_args()
    return do_check() if args.check else do_sync()


if __name__ == "__main__":
    sys.exit(main())
