#!/usr/bin/env python3
"""Build the versioned distribution artifact and its SHA-256 checksum.

The release workflow runs this on a ``v*`` tag. It writes two files into the
output directory:

    personal-agent-config-<version>.tar.gz   the repository at the tagged commit
    SHA256SUMS                               one line: <sha256>  <artifact name>

The archive is produced with ``git archive`` from ``HEAD``, so it contains only
committed, tracked content and is reproducible from the tag.

Usage:
    python3 release.py --version v1.0.0
    python3 release.py --version v1.0.0 --output dist
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

# A release tag such as v1.0.0 or v1.2.3-rc.1.
VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
ARCHIVE_STEM = "personal-agent-config-"
CHECKSUM_NAME = "SHA256SUMS"
REPO_ROOT = Path(__file__).resolve().parent


def archive_name(version: str) -> str:
    """Return the release archive filename for ``version``."""
    return f"{ARCHIVE_STEM}{version}.tar.gz"


def build(version: str, output: Path, repo: Path = REPO_ROOT) -> tuple[Path, Path, str]:
    """Build the archive and checksum file; return (archive, checksums, digest)."""
    if not VERSION_PATTERN.match(version):
        sys.exit(f"invalid version {version!r}; expected a tag like v1.2.3")

    output.mkdir(parents=True, exist_ok=True)
    name = archive_name(version)
    target = output / name
    prefix = f"{ARCHIVE_STEM}{version}/"

    result = subprocess.run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix={prefix}",
            "-o",
            str(target),
            "HEAD",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit("git archive failed:\n" + (result.stderr or "").strip())

    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    checksums = output / CHECKSUM_NAME
    checksums.write_text(f"{digest}  {name}\n", encoding="utf-8")
    return target, checksums, digest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the release archive and its SHA-256 checksum."
    )
    parser.add_argument(
        "--version", required=True, help="release tag, for example v1.0.0"
    )
    parser.add_argument(
        "--output", type=Path, default=REPO_ROOT / "dist", help="output directory"
    )
    args = parser.parse_args()

    target, checksums, digest = build(args.version, args.output)
    print(f"{digest}  {target.name}")
    print(f"wrote {target}")
    print(f"wrote {checksums}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
