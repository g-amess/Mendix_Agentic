"""Tests for adapters/lib/frontmatter.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from adapters.lib.frontmatter import parse_frontmatter, FrontmatterError  # noqa: E402


class TestScalars(unittest.TestCase):
    def test_plain_string(self):
        p = parse_frontmatter("---\nname: hello\n---\nbody\n", filename="x.md")
        self.assertEqual(p.data["name"], "hello")

    def test_single_quoted(self):
        p = parse_frontmatter("---\nname: 'hello world'\n---\n", filename="x.md")
        self.assertEqual(p.data["name"], "hello world")

    def test_double_quoted(self):
        p = parse_frontmatter('---\nname: "with: colon"\n---\n', filename="x.md")
        self.assertEqual(p.data["name"], "with: colon")

    def test_booleans(self):
        p = parse_frontmatter("---\na: true\nb: false\n---\n", filename="x.md")
        self.assertEqual(p.data, {"a": True, "b": False})

    def test_integer(self):
        p = parse_frontmatter("---\nn: 42\n---\n", filename="x.md")
        self.assertEqual(p.data["n"], 42)

    def test_colon_space_unquoted_rejected(self):
        with self.assertRaises(FrontmatterError) as ctx:
            parse_frontmatter("---\na: foo: bar\n---\n", filename="x.md")
        self.assertEqual(ctx.exception.line, 2)

    def test_null_rejected(self):
        with self.assertRaises(FrontmatterError) as ctx:
            parse_frontmatter("---\na: null\n---\n", filename="x.md")
        self.assertIn("null", ctx.exception.message)

    def test_float_rejected(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\na: 1.5\n---\n", filename="x.md")

    def test_multiline_rejected(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\na: |\n  foo\n---\n", filename="x.md")


class TestLists(unittest.TestCase):
    def test_flow_list(self):
        p = parse_frontmatter("---\nitems: [a, b, c]\n---\n", filename="x.md")
        self.assertEqual(p.data["items"], ["a", "b", "c"])

    def test_flow_list_quoted(self):
        p = parse_frontmatter('---\nitems: ["a, b", c]\n---\n', filename="x.md")
        self.assertEqual(p.data["items"], ["a, b", "c"])

    def test_flow_list_empty(self):
        p = parse_frontmatter("---\nitems: []\n---\n", filename="x.md")
        self.assertEqual(p.data["items"], [])

    def test_block_list(self):
        text = "---\nitems:\n  - a\n  - b\n---\n"
        p = parse_frontmatter(text, filename="x.md")
        self.assertEqual(p.data["items"], ["a", "b"])

    def test_unterminated_flow(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\na: [1, 2\n---\n", filename="x.md")


class TestStructure(unittest.TestCase):
    def test_body_start_line(self):
        p = parse_frontmatter("---\na: 1\n---\nhello\n", filename="x.md")
        self.assertEqual(p.data, {"a": 1})
        self.assertEqual(p.body_start_line, 4)

    def test_no_frontmatter(self):
        p = parse_frontmatter("hello body\n", filename="x.md")
        self.assertEqual(p.data, {})
        self.assertEqual(p.body_start_line, 1)

    def test_unclosed_frontmatter(self):
        with self.assertRaises(FrontmatterError) as ctx:
            parse_frontmatter("---\na: 1\n", filename="x.md")
        self.assertEqual(ctx.exception.line, 1)

    def test_duplicate_key(self):
        with self.assertRaises(FrontmatterError) as ctx:
            parse_frontmatter("---\na: 1\na: 2\n---\n", filename="x.md")
        self.assertEqual(ctx.exception.line, 3)

    def test_indented_toplevel_rejected(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\n  a: 1\n---\n", filename="x.md")


if __name__ == "__main__":
    unittest.main()
