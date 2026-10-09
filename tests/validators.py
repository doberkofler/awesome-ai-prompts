"""Repository-standard validators shared by the test suite and CI.

Each ``*_errors`` function returns a list of human-readable problems. An empty
list means the repository satisfies that standard. The validators only inspect
tracked Markdown, so temporary untracked files never affect CI.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_FRONTMATTER_DELIMITER = "---"
_KEY = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_HEADING = re.compile(r"^(#{1,6})\s")

DESCRIPTION_MAX_LENGTH = 1024


def tracked_markdown(root: Path = REPO_ROOT) -> list[Path]:
    """Return tracked Markdown paths, falling back to the working tree."""
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return [root / line for line in result.stdout.splitlines() if line.strip()]
    return sorted(p for p in root.rglob("*.md") if ".git" not in p.parts)


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    """Parse simple ``key: value`` frontmatter, including folded values.

    Returns ``(None, text)`` when the document has no opening/closing delimiter.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIMITER:
        return None, text
    closing = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == _FRONTMATTER_DELIMITER),
        None,
    )
    if closing is None:
        return None, text
    data: dict[str, str] = {}
    key: str | None = None
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if not line[0].isspace():
            match = _KEY.match(line)
            if match:
                key = match.group(1)
                data[key] = match.group(2).strip()
                continue
        if key is not None and line[0].isspace():
            data[key] = f"{data[key]} {line.strip()}".strip()
    return data, "\n".join(lines[closing + 1 :])


def strip_fenced_code(text: str) -> str:
    """Blank out fenced code blocks so links inside examples are ignored."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def frontmatter_errors(root: Path = REPO_ROOT) -> list[str]:
    """Validate command and skill frontmatter."""
    errors: list[str] = []
    for path in tracked_markdown(root):
        rel = path.relative_to(root)
        is_command = len(rel.parts) == 2 and rel.parts[0] == "commands"
        is_skill = (
            len(rel.parts) == 3
            and rel.parts[0] == "skills"
            and path.name == "SKILL.md"
        )
        if not (is_command or is_skill):
            continue

        data, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        if data is None:
            errors.append(f"{rel}: missing YAML frontmatter delimited by '---'")
            continue
        if not data.get("description"):
            errors.append(f"{rel}: frontmatter is missing a 'description'")

        if is_command:
            if not data.get("agent"):
                errors.append(f"{rel}: frontmatter is missing an 'agent'")
            continue

        expected = rel.parts[1]
        if data.get("name") != expected:
            errors.append(
                f"{rel}: frontmatter name {data.get('name')!r} "
                f"must match directory {expected!r}"
            )
        description = data.get("description", "").strip("'\"")
        if len(description) > DESCRIPTION_MAX_LENGTH:
            errors.append(
                f"{rel}: description is {len(description)} characters "
                f"(limit {DESCRIPTION_MAX_LENGTH})"
            )
        if data.get("disable-model-invocation") not in (None, "true"):
            errors.append(
                f"{rel}: 'disable-model-invocation' must be 'true' when present"
            )
    return errors


def markdown_structure_errors(root: Path = REPO_ROOT) -> list[str]:
    """Validate encoding, line endings, code fences, and heading nesting."""
    errors: list[str] = []
    for path in tracked_markdown(root):
        rel = path.relative_to(root)
        raw = path.read_bytes()
        if b"\r\n" in raw:
            errors.append(f"{rel}: contains CRLF line endings")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: is not valid UTF-8")
            continue
        if not text.strip():
            errors.append(f"{rel}: is empty")
            continue
        if not text.endswith("\n"):
            errors.append(f"{rel}: does not end with a newline")

        fence_count = sum(
            1 for line in text.splitlines() if line.lstrip().startswith("```")
        )
        if fence_count % 2:
            errors.append(f"{rel}: has an unclosed fenced code block")

        in_fence = False
        previous_level = 0
        for number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            match = _HEADING.match(line)
            if not match:
                continue
            level = len(match.group(1))
            if previous_level and level > previous_level + 1:
                errors.append(
                    f"{rel}:{number}: heading jumps from h{previous_level} to h{level}"
                )
            previous_level = level
    return errors


def internal_link_errors(root: Path = REPO_ROOT) -> list[str]:
    """Validate that repo-relative Markdown links resolve to existing paths."""
    errors: list[str] = []
    for path in tracked_markdown(root):
        rel = path.relative_to(root)
        text = strip_fenced_code(path.read_text(encoding="utf-8"))
        for raw_target in _LINK.findall(text):
            target = raw_target.strip()
            if not target:
                continue
            target = target.split()[0].strip("<>")
            if target.startswith(
                ("http://", "https://", "mailto:", "#", "tel:", "data:")
            ):
                continue
            relative = target.split("#", 1)[0]
            if not relative:
                continue
            if not (path.parent / relative).exists():
                errors.append(f"{rel}: link target does not exist: {target}")
    return errors


def _mentions(text: str, token: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text) is not None


def provenance_errors(root: Path = REPO_ROOT) -> list[str]:
    """Validate that every skill and document is accounted for in provenance."""
    errors: list[str] = []
    provenance = root / "PROVENANCE.md"
    if not provenance.is_file():
        return ["PROVENANCE.md is missing"]
    text = provenance.read_text(encoding="utf-8")

    skills = root / "skills"
    if skills.is_dir():
        for skill in sorted(skills.iterdir()):
            if not (skill / "SKILL.md").is_file():
                continue
            if not _mentions(text, skill.name):
                errors.append(f"PROVENANCE.md does not cover skill: {skill.name}")

    docs = root / "docs"
    if docs.is_dir():
        for doc in sorted(docs.glob("*.md")):
            if not _mentions(text, doc.name):
                errors.append(f"PROVENANCE.md does not cover document: {doc.name}")

    commands = root / "commands"
    if commands.is_dir():
        for command in sorted(commands.glob("*.md")):
            if not _mentions(text, command.name):
                errors.append(f"PROVENANCE.md does not cover command: {command.name}")
    return errors


def distributed_files(root: Path = REPO_ROOT) -> list[Path]:
    """Return every distributed entry point: rule, command, and skill."""
    files: list[Path] = []
    for pattern in ("docs/*.md", "commands/*.md"):
        files.extend(sorted(root.glob(pattern)))
    skills = root / "skills"
    if skills.is_dir():
        files.extend(
            skill / "SKILL.md"
            for skill in sorted(skills.iterdir())
            if (skill / "SKILL.md").is_file()
        )
    return files


def readme_index_errors(root: Path = REPO_ROOT) -> list[str]:
    """Validate that every distributed file is linked from the README index."""
    errors: list[str] = []
    readme = root / "README.md"
    if not readme.is_file():
        return ["README.md is missing"]
    text = strip_fenced_code(readme.read_text(encoding="utf-8"))
    targets: set[Path] = set()
    for raw_target in _LINK.findall(text):
        target = raw_target.strip()
        if not target:
            continue
        target = target.split()[0].strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#", "tel:", "data:")):
            continue
        relative = target.split("#", 1)[0]
        if relative:
            targets.add((readme.parent / relative).resolve())
    for path in distributed_files(root):
        if path.resolve() not in targets:
            errors.append(
                f"README.md does not link distributed file: {path.relative_to(root)}"
            )
    return errors


def all_errors(root: Path = REPO_ROOT) -> dict[str, list[str]]:
    """Run every validator and return the non-empty result sets."""
    return {
        "frontmatter": frontmatter_errors(root),
        "markdown structure": markdown_structure_errors(root),
        "internal links": internal_link_errors(root),
        "provenance coverage": provenance_errors(root),
        "readme index": readme_index_errors(root),
    }
