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


if __name__ == "__main__":
    unittest.main()
