#!/usr/bin/env python3
"""Distribute the canonical AI rules to the local agent configurations.

Canonical source: https://github.com/doberkofler/awesome-ai-prompts

The same content is written to each supported agent's user-level location:

  opencode    rules:    ~/.config/opencode/docs/*.md        (per topic)
              commands: ~/.config/opencode/commands/*.md
              skills:   ~/.config/opencode/skills/<name>/
  Claude Code rules:    ~/.claude/rules/*.md                (per topic)
              commands: ~/.claude/commands/*.md
              skills:   ~/.claude/skills/<name>/
  Codex       rules:    ~/.codex/AGENTS.md                   (concatenated)
              commands: ~/.codex/prompts/*.md                (deprecated by Codex)
              skills:   ~/.agents/skills/<name>/
  Pi          rules:    ~/.pi/agent/AGENTS.md                (concatenated)
              commands: ~/.pi/agent/prompts/*.md
              skills:   ~/.pi/agent/skills/<name>/

Usage:
    python3 sync_ai_rules.py            # pull latest and distribute
    python3 sync_ai_rules.py --check    # report whether the install is current

Network access is required to clone/pull. Offline runs reuse the local copy.
"""
from __future__ import annotations

import argparse
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
        "docs": HOME / ".config" / "opencode" / "docs",
        "commands": HOME / ".config" / "opencode" / "commands",
        "skills": HOME / ".config" / "opencode" / "skills",
    },
    "claude": {
        "docs": HOME / ".claude" / "rules",
        "commands": HOME / ".claude" / "commands",
        "skills": HOME / ".claude" / "skills",
    },
    "codex": {
        "agents": HOME / ".codex" / "AGENTS.md",
        "commands": HOME / ".codex" / "prompts",
        "skills": HOME / ".agents" / "skills",
        "config": HOME / ".codex" / "config.toml",
    },
    "pi": {
        "agents": HOME / ".pi" / "agent" / "AGENTS.md",
        "commands": HOME / ".pi" / "agent" / "prompts",
        "skills": HOME / ".pi" / "agent" / "skills",
    },
}

CONCAT_AGENTS = ("codex", "pi")
PER_TOPIC_AGENTS = ("opencode", "claude")
ALL_AGENTS = ("opencode", "claude", "codex", "pi")

CODEX_DEFAULT_MAX_BYTES = 32768
CODEX_RECOMMENDED_MAX_BYTES = 65536


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


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def distribute_rules(repo: Path, sha: str) -> str:
    docs = doc_files(repo)

    for agent in PER_TOPIC_AGENTS:
        dest = TARGETS[agent]["docs"]
        dest.mkdir(parents=True, exist_ok=True)
        for f in docs:
            copy_file(f, dest / f.name)
        print(f"rules  -> {dest} ({len(docs)} files)")

    parts = [f"<!-- awesome-ai-prompts {sha} -->", ""]
    for f in docs:
        parts.append(f.read_text(encoding="utf-8").rstrip() + "\n")
    combined = "\n".join(parts)

    for agent in CONCAT_AGENTS:
        dest = TARGETS[agent]["agents"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(combined, encoding="utf-8")
        print(f"rules  -> {dest} ({len(combined.encode('utf-8'))} bytes)")

    return combined


def distribute_skills(repo: Path) -> None:
    src = repo / "skills"
    if not src.is_dir():
        return
    skills = [d for d in sorted(src.iterdir()) if d.is_dir() and not d.name.startswith(".")]
    for agent in ALL_AGENTS:
        dest = TARGETS[agent]["skills"]
        dest.mkdir(parents=True, exist_ok=True)
        for skill in skills:
            target = dest / skill.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill, target)
        print(f"skills -> {dest} ({len(skills)} dirs)")


def distribute_commands(repo: Path) -> None:
    src = repo / "commands"
    if not src.is_dir():
        return
    files = sorted(p for p in src.glob("*.md") if p.is_file())
    for agent in ALL_AGENTS:
        dest = TARGETS[agent]["commands"]
        dest.mkdir(parents=True, exist_ok=True)
        for f in files:
            copy_file(f, dest / f.name)
        print(f"cmds   -> {dest} ({len(files)} files)")


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
    path = TARGETS["codex"]["agents"]
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


def do_sync() -> int:
    repo = resolve_repo(pull=True)
    sha = git_short_sha(repo)
    print(f"source: {repo} @ {sha}\n")
    combined = distribute_rules(repo, sha)
    distribute_skills(repo)
    distribute_commands(repo)
    warn_codex_size(combined)
    write_state(repo)
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
        return 0
    print("status:    OUT OF DATE - run: python3 ~/.ai-rules/src/sync_ai_rules.py")
    return 1


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
