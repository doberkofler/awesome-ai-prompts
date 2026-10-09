"""Isolated harness for exercising ``sync_ai_rules.py`` as a subprocess.

The installer resolves every target through ``Path.home()``. Running a copy of
the script with ``HOME`` pointed at a temporary directory therefore exercises
the real code path without touching the operator's home directory. The source
tree is also a temporary fixture, so tests never clone or pull.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_NAME = "sync_ai_rules.py"

# Mirror the target layout declared in sync_ai_rules.py.
RULE_PATHS = {
    "opencode": Path(".config/opencode/AGENTS.md"),
    "claude": Path(".claude/CLAUDE.md"),
    "codex": Path(".codex/AGENTS.md"),
    "pi": Path(".pi/agent/AGENTS.md"),
}
COMMAND_DIRS = {
    "opencode": Path(".config/opencode/commands"),
    "claude": Path(".claude/commands"),
    "codex": Path(".codex/prompts"),
    "pi": Path(".pi/agent/prompts"),
}
SKILL_DIRS = (
    Path(".agents/skills"),
    Path(".claude/skills"),
)

# Real-home paths the installer must never mutate during tests.
REAL_HOME_TARGETS = (
    *RULE_PATHS.values(),
    *COMMAND_DIRS.values(),
    *SKILL_DIRS,
    Path(".ai-rules"),
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path, relatives: tuple[Path, ...]) -> dict[str, str]:
    """Hash every file under ``root / relative`` for change detection."""
    state: dict[str, str] = {}
    for relative in relatives:
        base = root / relative
        if not base.exists():
            continue
        state[str(relative)] = "<dir>" if base.is_dir() else _digest(base)
        if base.is_dir():
            for child in sorted(base.rglob("*")):
                if child.is_file():
                    state[str(child.relative_to(root))] = _digest(child)
    return state


class InstallerFixture:
    """A temporary source repository plus a temporary ``HOME``."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.src = root / "src"
        self.home = root / "home"
        self.src.mkdir(parents=True)
        self.home.mkdir(parents=True)
        shutil.copy2(REPO_ROOT / SCRIPT_NAME, self.src / SCRIPT_NAME)
        for directory in ("docs", "skills", "commands"):
            (self.src / directory).mkdir()

    # -- source mutation -------------------------------------------------
    def set_doc(self, name: str, text: str) -> None:
        (self.src / "docs" / name).write_text(text, encoding="utf-8")

    def remove_doc(self, name: str) -> None:
        (self.src / "docs" / name).unlink()

    def set_skill(self, name: str, files: dict[str, str]) -> None:
        skill = self.src / "skills" / name
        if skill.exists():
            shutil.rmtree(skill)
        for relative, text in files.items():
            target = skill / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

    def remove_skill(self, name: str) -> None:
        shutil.rmtree(self.src / "skills" / name)

    def set_command(self, name: str, text: str) -> None:
        (self.src / "commands" / name).write_text(text, encoding="utf-8")

    def remove_command(self, name: str) -> None:
        (self.src / "commands" / name).unlink()

    # -- execution -------------------------------------------------------
    def run(self) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        for variable in ("XDG_CONFIG_HOME", "XDG_DATA_HOME"):
            env.pop(variable, None)
        return subprocess.run(
            [sys.executable, str(self.src / SCRIPT_NAME)],
            cwd=str(self.src),
            env=env,
            capture_output=True,
            text=True,
        )

    # -- installed paths -------------------------------------------------
    def rules(self, agent: str) -> Path:
        return self.home / RULE_PATHS[agent]

    def commands_dir(self, agent: str) -> Path:
        return self.home / COMMAND_DIRS[agent]

    def skill(self, directory: Path, name: str) -> Path:
        return self.home / directory / name

    def managed_skills_file(self) -> Path:
        return self.home / ".ai-rules" / "managed-skills"

    def installed_state_file(self) -> Path:
        return self.home / ".ai-rules" / "installed"
