"""Tests for bin/doctor.py version gates (ADR-0025, ADR-0026)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("doctor", REPO_ROOT / "bin" / "doctor.py")
doctor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(doctor)


class TestClaudeCodeMinimum(unittest.TestCase):
    def test_below_minimum_fails_with_update_fix(self):
        r = doctor._claude_code_result("2.1.128 (Claude Code)")
        self.assertEqual(r.status, "FAIL")
        self.assertIn("2.1.281", r.detail)
        self.assertIn("claude update", r.fix)
        self.assertIn("VS Code", r.fix)

    def test_at_minimum_passes(self):
        self.assertEqual(doctor._claude_code_result("2.1.281 (Claude Code)").status, "PASS")

    def test_above_minimum_passes(self):
        self.assertEqual(doctor._claude_code_result("2.1.305 (Claude Code)").status, "PASS")

    def test_unparseable_warns(self):
        self.assertEqual(doctor._claude_code_result("Claude Code").status, "WARN")


class TestHookPython(unittest.TestCase):
    def _check(self, which: dict, run_result):
        with mock.patch.object(doctor.shutil, "which", side_effect=lambda n: which.get(n)), \
                mock.patch.object(doctor, "_run", return_value=run_result):
            return doctor.check_hook_python()

    def test_missing_python_fails_when_claude_present(self):
        r = self._check({"claude": "/bin/claude"}, (127, "", "not found"))
        self.assertEqual(r.status, "FAIL")

    def test_missing_python_warns_without_claude(self):
        self.assertEqual(self._check({}, (127, "", "not found")).status, "WARN")

    def test_old_python_fails(self):
        r = self._check({"claude": "/bin/claude", "python": "/bin/python"}, (0, "3.9.18", ""))
        self.assertEqual(r.status, "FAIL")

    def test_store_alias_stub_fails(self):
        # The Windows App execution alias prints a message and exits 9009.
        r = self._check({"claude": "c", "python": "p"}, (9009, "", "Python was not found"))
        self.assertEqual(r.status, "FAIL")

    def test_supported_python_passes(self):
        r = self._check({"claude": "c", "python": "p"}, (0, "3.10.0", ""))
        self.assertEqual(r.status, "PASS")


if __name__ == "__main__":
    unittest.main()
