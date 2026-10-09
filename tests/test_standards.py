"""Static repository standards: Markdown, frontmatter, links, provenance."""
from __future__ import annotations

import unittest

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
