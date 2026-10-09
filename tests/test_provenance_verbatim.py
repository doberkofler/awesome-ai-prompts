"""Verify the ``Verbatim`` skill claims in PROVENANCE.md against upstream.

The audited snapshot is pinned by commit SHA, so the comparison is deterministic.
The test downloads the snapshot tarball; when the network is unavailable it skips
rather than reporting a false failure.
"""
from __future__ import annotations

import io
import re
import tarfile
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = REPO_ROOT / "PROVENANCE.md"
SNAPSHOT_URL = "https://codeload.github.com/mattpocock/skills/tar.gz/{sha}"

_VERBATIM_LINK = re.compile(
    r"\[(?P<name>[^\]]+)\]\("
    r"https://github\.com/mattpocock/skills/tree/"
    r"(?P<sha>[0-9a-f]{7,40})/(?P<path>skills/[^)]+)\)"
)
_AUDITED_SNAPSHOT = re.compile(
    r"Last fully audited snapshot:\s*\[`([0-9a-f]+)`\]"
    r"\(https://github\.com/mattpocock/skills/commit/([0-9a-f]+)\)"
)


def _section(text: str, heading: str) -> str:
    """Return the body of ``heading`` up to the next H2/H3 heading."""
    start = text.index(heading) + len(heading)
    rest = text[start:]
    match = re.search(r"^#{2,3} ", rest, re.MULTILINE)
    return rest[: match.start()] if match else rest


def _verbatim_entries() -> list[tuple[str, str, str]]:
    """Return ``(name, sha, upstream_path)`` for each Verbatim skill bullet."""
    body = _section(PROVENANCE.read_text(encoding="utf-8"), "### Verbatim skills")
    return [
        (name.strip("`"), sha, path)
        for name, sha, path in _VERBATIM_LINK.findall(body)
    ]


class VerbatimProvenanceTests(unittest.TestCase):
    def test_verbatim_skills_share_audited_snapshot(self) -> None:
        audited = _AUDITED_SNAPSHOT.search(PROVENANCE.read_text(encoding="utf-8"))
        self.assertIsNotNone(audited, "audited snapshot reference not found")
        assert audited is not None
        entries = _verbatim_entries()
        self.assertTrue(entries, "no Verbatim skills parsed from PROVENANCE.md")
        for _, sha, _ in entries:
            self.assertTrue(
                audited.group(2).startswith(sha),
                f"Verbatim link {sha} is not the audited snapshot",
            )

    def test_verbatim_skills_match_snapshot(self) -> None:
        by_sha: dict[str, list[tuple[str, str]]] = {}
        for name, sha, path in _verbatim_entries():
            by_sha.setdefault(sha, []).append((name, path))

        for sha, skills in by_sha.items():
            with self.subTest(snapshot=sha):
                extracted = self._download(sha)
                upstream_root = extracted / f"skills-{sha}"
                for name, path in skills:
                    with self.subTest(skill=name):
                        self._assert_identical(name, upstream_root / path)

    def _download(self, sha: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        target = Path(tmp.name)
        try:
            with urllib.request.urlopen(
                SNAPSHOT_URL.format(sha=sha), timeout=60
            ) as response:
                payload = response.read()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise unittest.SkipTest(f"network unavailable: {exc}") from exc
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
            tar.extractall(target, filter="data")
        return target

    def _assert_identical(self, name: str, upstream: Path) -> None:
        local = REPO_ROOT / "skills" / name
        self.assertTrue(local.is_dir(), f"missing local skill: {name}")
        self.assertTrue(upstream.is_dir(), f"missing upstream path: {upstream}")
        upstream_files = _payload(upstream)
        local_files = _payload(local)
        self.assertEqual(
            sorted(upstream_files),
            sorted(local_files),
            f"{name}: payload file set differs from the audited snapshot",
        )
        for rel in sorted(upstream_files):
            self.assertEqual(
                upstream_files[rel],
                local_files[rel],
                f"{name}/{rel}: content differs from the audited snapshot",
            )


def _payload(root: Path) -> dict[str, bytes]:
    """Return retained payload files, excluding omitted sidecars and metadata."""
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.name == ".DS_Store" or rel.parts[0] == "agents":
            continue
        files[str(rel)] = path.read_bytes()
    return files


if __name__ == "__main__":
    unittest.main()
