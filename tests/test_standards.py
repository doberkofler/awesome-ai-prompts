"""Static repository standards: Markdown, frontmatter, links, provenance."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests import validators


class FrontmatterTests(unittest.TestCase):
    def test_command_and_skill_frontmatter(self) -> None:
        self.assertEqual([], validators.frontmatter_errors())


class MarkdownStructureTests(unittest.TestCase):
    def test_encoding_fences_and_headings(self) -> None:
        self.assertEqual([], validators.markdown_structure_errors())


class InternalLinkTests(unittest.TestCase):
    def test_relative_links_resolve(self) -> None:
        self.assertEqual([], validators.internal_link_errors())


class ProvenanceTests(unittest.TestCase):
    def test_every_skill_and_document_is_covered(self) -> None:
        self.assertEqual([], validators.provenance_errors())


class ReadmeIndexTests(unittest.TestCase):
    def test_every_distributed_file_is_indexed(self) -> None:
        self.assertEqual([], validators.readme_index_errors())

    def test_index_validator_flags_unlisted_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("x\n", encoding="utf-8")
            (root / "README.md").write_text("# title\n", encoding="utf-8")
            errors = validators.readme_index_errors(root)
            self.assertTrue(any("docs/a.md" in error for error in errors), errors)

    def test_index_validator_accepts_linked_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("x\n", encoding="utf-8")
            (root / "README.md").write_text("[a](docs/a.md)\n", encoding="utf-8")
            self.assertEqual([], validators.readme_index_errors(root))


class IdentityTests(unittest.TestCase):
    def test_repository_identity_is_consistent(self) -> None:
        root = validators.REPO_ROOT
        sync = (root / "sync_ai_rules.py").read_text(encoding="utf-8")
        release = (root / "release.py").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'REPO_URL = "https://github.com/doberkofler/personal-agent-config.git"',
            sync,
        )
        self.assertIn('ARCHIVE_STEM = "personal-agent-config-"', release)
        self.assertIn("dist/personal-agent-config-*.tar.gz", workflow)
        self.assertTrue(
            readme.startswith("# Personal Agent Configuration\n"), readme[:40]
        )
        self.assertNotIn("awesome-ai-prompts", readme)


class SelfCheckTests(unittest.TestCase):
    """Guard the validators against silently passing on broken input."""

    def test_frontmatter_detects_missing_keys(self) -> None:
        data, _ = validators.parse_frontmatter("---\nname: x\n---\nbody\n")
        self.assertIsNotNone(data)
        self.assertNotIn("description", data or {})

    def test_frontmatter_parses_folded_values(self) -> None:
        text = "---\ndescription: first\n  second\nagent: plan\n---\n"
        data, _ = validators.parse_frontmatter(text)
        self.assertEqual("first second", (data or {}).get("description"))
        self.assertEqual("plan", (data or {}).get("agent"))

    def test_link_validator_ignores_fenced_examples(self) -> None:
        text = "```\n[missing](./nope.md)\n```\n"
        self.assertEqual("", validators.strip_fenced_code(text).strip())


if __name__ == "__main__":
    unittest.main()
