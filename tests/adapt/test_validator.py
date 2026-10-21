"""Tests for adapters/validate.py.

One test per failure rule, plus a happy-path test against the valid fixture.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from adapters.validate import Validator  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "core"


def _run(fixture_name: str) -> Validator:
    d = FIXTURES / fixture_name
    v = Validator(core_dir=d, policy_dir=d)
    v.load_registries()
    skills_dir = d / "skills"
    if skills_dir.exists():
        for p in sorted(skills_dir.glob("*/SKILL.md")):
            v.validate_skill(p)
    roles_dir = d / "roles"
    if roles_dir.exists():
        for p in sorted(roles_dir.glob("*.md")):
            if p.name == "README.md":
                continue
            v.validate_role(p)
    v.cross_check_roles()
    return v


class TestValid(unittest.TestCase):
    def test_valid_fixture_passes(self):
        v = _run("valid")
        self.assertEqual(v.issues, [], msg=[str(i) for i in v.issues])
        self.assertIn("orchestrator", v.roles)
        self.assertIn("writer", v.roles)
        self.assertIn("intake", v.skills)
        self.assertIn("mdl-draft", v.skills)


class TestInvalidRoles(unittest.TestCase):
    def _assert_fails_with(self, fixture: str, substring: str):
        v = _run(fixture)
        joined = "\n".join(str(i) for i in v.issues)
        self.assertTrue(
            any(substring in str(i).lower() for i in v.issues),
            msg=f"expected {substring!r} in issues; got: {joined}",
        )

    def test_unknown_frontmatter_key(self):
        self._assert_fails_with("invalid_frontmatter_unknown_key", "unknown")

    def test_name_mismatch(self):
        self._assert_fails_with("invalid_name_mismatch", "filename")

    def test_spoke_with_delegates(self):
        self._assert_fails_with("invalid_spoke_delegates", "spoke")

    def test_read_role_with_owns(self):
        self._assert_fails_with("invalid_read_owns", "owns: []")

    def test_write_role_no_owns(self):
        self._assert_fails_with("invalid_write_no_owns", "write")

    def test_duplicate_class(self):
        self._assert_fails_with("invalid_duplicate_class", "owned by multiple")

    def test_bad_capability(self):
        self._assert_fails_with("invalid_bad_capability", "not in core/capabilities.json")

    def test_undefined_write_class(self):
        self._assert_fails_with("invalid_undefined_write_class", "not in policy/write-classes.json")

    def test_hub_delegates_to_hub(self):
        self._assert_fails_with("invalid_hub_delegates_hub", "not a spoke")

    def test_description_too_long(self):
        self._assert_fails_with("invalid_description_too_long", "max 400")

    def test_missing_body_section(self):
        self._assert_fails_with("invalid_missing_section", "procedure")

    def test_ask_human_on_spoke(self):
        self._assert_fails_with("invalid_ask_human_on_spoke", "ask-human")


class TestInvalidSkills(unittest.TestCase):
    def _assert_fails_with(self, fixture: str, substring: str):
        v = _run(fixture)
        joined = "\n".join(str(i) for i in v.issues)
        self.assertTrue(
            any(substring in str(i).lower() for i in v.issues),
            msg=f"expected {substring!r} in issues; got: {joined}",
        )

    def test_nonspec_key(self):
        self._assert_fails_with("invalid_skill_nonspec_key", "non-spec")

    def test_missing_name(self):
        self._assert_fails_with("invalid_skill_missing_name", "name")

    def test_name_mismatch(self):
        self._assert_fails_with("invalid_skill_name_mismatch", "parent")

    def test_sidecar_unknown_key(self):
        # A misspelt Claude field would otherwise be emitted top-level and
        # silently ignored by Claude Code (ADR-0027).
        self._assert_fails_with("invalid_skill_sidecar_unknown_key", "unknown key")


class TestHubFixture(unittest.TestCase):
    def test_hub_two_spokes_passes(self):
        v = _run("hub_two_spokes")
        self.assertEqual(v.issues, [], msg=[str(i) for i in v.issues])


class TestRealCore(unittest.TestCase):
    """The real core/ (empty of roles in phase 2) must validate cleanly."""

    def test_real_core_passes(self):
        v = Validator(core_dir=REPO_ROOT / "core", policy_dir=REPO_ROOT / "policy")
        self.assertEqual(v.run(), 0)


if __name__ == "__main__":
    unittest.main()
