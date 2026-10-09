"""Release artifact tests for ``release.py``.

The script builds from ``git archive HEAD``, so these tests exercise the real
release path against the repository checkout without writing into it.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_SCRIPT = REPO_ROOT / "release.py"
VERSION = "v0.0.0-test"


def run_release(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RELEASE_SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


class ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.output = Path(self._tmp.name)

    def test_build_produces_archive_and_checksum(self) -> None:
        result = run_release("--version", VERSION, "--output", str(self.output))
        self.assertEqual(0, result.returncode, result.stderr)

        archive = self.output / f"personal-agent-config-{VERSION}.tar.gz"
        checksums = self.output / "SHA256SUMS"
        self.assertTrue(archive.is_file())
        self.assertTrue(checksums.is_file())

        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.assertIn(digest, result.stdout)
        self.assertEqual(
            f"{digest}  {archive.name}\n", checksums.read_text(encoding="utf-8")
        )

    def test_archive_contains_tracked_content_at_release_root(self) -> None:
        result = run_release("--version", VERSION, "--output", str(self.output))
        self.assertEqual(0, result.returncode, result.stderr)
        archive = self.output / f"personal-agent-config-{VERSION}.tar.gz"

        with tarfile.open(archive, "r:gz") as tar:
            names = set(tar.getnames())

        prefix = f"personal-agent-config-{VERSION}/"
        self.assertIn(prefix + "sync_ai_rules.py", names)
        self.assertIn(prefix + "docs/lint-rules.md", names)
        self.assertIn(prefix + "LICENSE", names)
        # git archive includes only tracked content, so the temporary plan file
        # can never ship in a release.
        self.assertNotIn(prefix + "todo.md", names)

    def test_invalid_version_is_rejected(self) -> None:
        result = run_release("--version", "1.0.0", "--output", str(self.output))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid version", result.stderr)


if __name__ == "__main__":
    unittest.main()
