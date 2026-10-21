"""Tests for .github/scripts/check_mxcli_tree.py (no network, no mxcli)."""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "check_mxcli_tree", REPO_ROOT / ".github" / "scripts" / "check_mxcli_tree.py"
)
tree = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tree)

GOOD = b"pinned-binary-bytes"
PIN = {
    "asset": "mxcli-linux-amd64",
    "sha256": hashlib.sha256(GOOD).hexdigest(),
    "size_bytes": len(GOOD),
    "download_url": "https://example.invalid/mxcli",
}


class TestCachedBinary(unittest.TestCase):
    """ADR-0032: a cache restore is re-verified before the binary runs."""

    def test_verified_cache_hit_skips_download(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / PIN["asset"]
            dest.write_bytes(GOOD)
            with mock.patch.object(tree, "_download_and_verify") as dl:
                tree._obtain_verified(PIN, dest)
            dl.assert_not_called()
            self.assertEqual(dest.read_bytes(), GOOD)

    def test_tampered_cache_is_discarded_and_redownloaded(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / PIN["asset"]
            dest.write_bytes(b"tampered")
            with mock.patch.object(tree, "_http_get", return_value=GOOD) as get:
                tree._obtain_verified(PIN, dest)
            get.assert_called_once()
            self.assertEqual(dest.read_bytes(), GOOD)

    def test_download_with_wrong_hash_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / PIN["asset"]
            with mock.patch.object(tree, "_http_get", return_value=b"evil"):
                with self.assertRaises(SystemExit):
                    tree._obtain_verified(PIN, dest)
            self.assertFalse(dest.exists())


# cobra's help block: names padded to the longest (min 11), then ONE space.
# The "Available Commands" blocks are verbatim from the v0.26.0 release
# binary (mxcli-windows-amd64.exe) `diag --help` and `fix --help`.
DIAG_HELP = """Usage:
  mxcli diag [flags]
  mxcli diag [command]

Available Commands:
  loop-report    Report where this project's mxcli calls went, from the session logs
  session-report Report where an agent session's tool calls and tokens went, from its transcript

Flags:
  -h, --help   help for diag
"""

FIX_HELP = """Available Commands:
  design-properties Update renamed design properties (clears CE6087) without collapsing MPR v2
  hashes            Verify (and with --repair, rewrite) the MPR v2 ContentsHash index
  property-sets     Give every stored unit the property names Studio Pro writes (unblocks mx diff / merge)
  widgets           Resync widget definitions (clears CE0463) without collapsing MPR v2

"""


class TestHelpParsing(unittest.TestCase):
    """Phase 2.2: the longest name in a block is followed by ONE space."""

    def _subs(self, text):
        fake = mock.Mock(stdout=text, stderr="")
        with mock.patch.object(tree.subprocess, "run", return_value=fake):
            return tree._list_subcommands(Path("mxcli"), ["x"])

    def test_longest_name_with_single_space_is_found(self):
        self.assertEqual(self._subs(DIAG_HELP), ["loop-report", "session-report"])

    def test_fix_block(self):
        self.assertEqual(
            self._subs(FIX_HELP),
            ["design-properties", "hashes", "property-sets", "widgets"],
        )

    def test_decodes_utf8(self):
        # Windows' default code page cannot decode some help text (phase 2.2).
        with mock.patch.object(tree.subprocess, "run") as run:
            run.return_value = mock.Mock(stdout="", stderr="")
            tree._list_subcommands(Path("mxcli"), [])
        self.assertEqual(run.call_args.kwargs.get("encoding"), "utf-8")


class TestCompare(unittest.TestCase):
    """ADR-0036: only hidden or build-conditional rows may be absent."""

    INV = {
        "help": {}, "list": {},
        "show": {"class": "READ"},
        "secret": {"class": "WRITE", "hidden": True},
        "tunnel": {"class": "WRITE", "build_condition": "linux"},
        "gone": {"class": "WRITE"},
    }

    def test_absent_unmarked_row_is_an_error(self):
        missing, extra, excused = tree.compare({"show", "new"}, self.INV)
        self.assertEqual(missing, ["new"])
        self.assertEqual(extra, ["gone"])
        self.assertEqual(excused, ["secret", "tunnel"])

    def test_alias_and_help_ignored(self):
        _, extra, _ = tree.compare({"show", "gone"}, self.INV)
        self.assertEqual(extra, [])


class TestInventoryMarkdown(unittest.TestCase):
    """ADR-0035: the §2 tables are generated from the JSON; drift fails."""

    def test_markdown_matches_json(self):
        spec = importlib.util.spec_from_file_location(
            "render", REPO_ROOT / ".github" / "scripts" / "render_mxcli_inventory.py"
        )
        render = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render)
        self.assertEqual(render.main(["--check"]), 0)

    def test_every_row_has_class_source_and_side_effects(self):
        import json
        rows = json.loads(
            (REPO_ROOT / "policy" / "mxcli-commands.json").read_text(encoding="utf-8")
        )["commands"]
        for path, row in rows.items():
            self.assertIn(row.get("class"), {"READ", "WRITE"}, msg=path)
            self.assertTrue(row.get("source"), msg=path)
            self.assertIsInstance(row.get("side_effects"), list, msg=path)
            if row.get("hidden") or row.get("build_condition"):
                self.assertIn("#L", row["source"], msg=f"{path}: cite the source line")


if __name__ == "__main__":
    unittest.main()
