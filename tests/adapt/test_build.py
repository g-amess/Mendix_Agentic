"""Tests for adapters/claude/build.py.

Covers:
- Capability mapping (role capabilities → Claude Code tools).
- Model-tier mapping (fast/standard/deep → haiku/sonnet/opus).
- Ownership generation (ADR-0019).
- Skill sidecar merge.
- Drift check (--check mode).
- Hooks JSON shape.
- Project settings template content.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from adapters.claude import build as b  # noqa: E402
from adapters.lib.frontmatter import parse_frontmatter  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "core" / "valid"


def _build_into_tmp() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="mxagent-build-"))
    # Build using the valid fixture
    b.build(
        core_dir=FIXTURE,
        policy_dir=REPO_ROOT / "policy",
        out_root=tmp / "mendix-agentic",
        version="test-0.0.0",
    )
    return tmp


class TestBuildFromFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = _build_into_tmp()
        cls.plugin = cls.tmp / "mendix-agentic"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_plugin_manifest(self):
        pj = json.loads((self.plugin / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(pj["name"], "mendix-agentic")
        self.assertEqual(pj["version"], "test-0.0.0")

    def test_hooks_shape(self):
        hj = json.loads((self.plugin / "hooks" / "hooks.json").read_text())
        self.assertIn("PreToolUse", hj["hooks"])
        pre = hj["hooks"]["PreToolUse"][0]
        self.assertEqual(
            pre["matcher"], "Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit"
        )
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", pre["hooks"][0]["command"])
        self.assertIn("python", pre["hooks"][0]["command"].split()[0])

    def test_agent_tools_mapped(self):
        txt = (self.plugin / "agents" / "orchestrator.md").read_text()
        fm = parse_frontmatter(txt, filename="orchestrator.md").data
        # orchestrator has capabilities: read-files, search-files,
        # edit-artefacts, mxcli-read, delegate, ask-human
        # → tools: Read, Grep, Glob, Edit, Write, MultiEdit, Bash,
        #          AskUserQuestion, Agent(analyst,writer)
        tools = fm["tools"]
        for expected in (
            "Read", "Grep", "Glob", "Edit", "Write", "MultiEdit", "Bash",
            "AskUserQuestion",
        ):
            self.assertIn(expected, tools, msg=f"missing {expected}")
        self.assertTrue(
            any("Agent(" in t for t in tools), msg=f"missing Agent(...) in {tools}"
        )
        # Never emit PowerShell (ADR-0016).
        self.assertNotIn("PowerShell", tools)

    def test_model_tier_mapped(self):
        orch = parse_frontmatter(
            (self.plugin / "agents" / "orchestrator.md").read_text(),
            filename="x",
        ).data
        self.assertEqual(orch["model"], "opus")  # deep → opus
        writer = parse_frontmatter(
            (self.plugin / "agents" / "writer.md").read_text(), filename="x"
        ).data
        self.assertEqual(writer["model"], "opus")  # deep → opus
        analyst = parse_frontmatter(
            (self.plugin / "agents" / "analyst.md").read_text(), filename="x"
        ).data
        self.assertEqual(analyst["model"], "sonnet")  # standard → sonnet

    def test_plugin_subagent_ignored_fields_absent(self):
        """Plugin subagents ignore `hooks`, `mcpServers`, `permissionMode` — the
        adapter does not emit them per code.claude.com/docs/en/sub-agents."""
        for role in ("orchestrator.md", "analyst.md", "writer.md"):
            fm = parse_frontmatter(
                (self.plugin / "agents" / role).read_text(), filename=role
            ).data
            for forbidden in ("hooks", "mcpServers", "permissionMode"):
                self.assertNotIn(forbidden, fm, msg=f"{role} has forbidden {forbidden}")

    def test_ownership_generated(self):
        own = json.loads((self.plugin / "policy" / "ownership.json").read_text())
        self.assertIn("GENERATED", own["_comment"])
        # Only `writer` has access: write + owns
        self.assertEqual(set(own["agents"].keys()), {"writer"})
        self.assertEqual(
            sorted(own["agents"]["writer"]["allow"]), ["model.domain", "model.logic"]
        )

    def test_skill_copied(self):
        self.assertTrue((self.plugin / "skills" / "intake" / "SKILL.md").exists())
        self.assertTrue((self.plugin / "skills" / "mdl-draft" / "SKILL.md").exists())

    def test_skill_sidecar_merged_into_metadata(self):
        md = (self.plugin / "skills" / "mdl-draft" / "SKILL.md").read_text()
        fm = parse_frontmatter(md, filename="SKILL.md").data
        # Sidecar merged under metadata.claude as a JSON string
        self.assertIn("metadata", fm)
        self.assertIn("claude", fm["metadata"])
        claude_blob = json.loads(fm["metadata"]["claude"])
        self.assertTrue(claude_blob["user-invocable"])
        self.assertIn("Bash(mxcli:*)", claude_blob["allowed-tools"])

    def test_policy_copied(self):
        self.assertTrue((self.plugin / "policy" / "mxcli_guard.py").exists())
        self.assertTrue((self.plugin / "policy" / "mxcli-commands.json").exists())
        self.assertTrue((self.plugin / "policy" / "stop-operations.json").exists())


class TestCheckMode(unittest.TestCase):
    def test_check_passes_on_fresh_build(self):
        # Build in-place, then run --check: should be clean.
        from adapters.claude.build import build, check
        version = b._load_version(REPO_ROOT)
        committed_out = REPO_ROOT / "plugins" / "mendix-agentic"
        build(
            core_dir=REPO_ROOT / "core",
            policy_dir=REPO_ROOT / "policy",
            out_root=committed_out,
            version=version,
        )
        rc = check(
            core_dir=REPO_ROOT / "core",
            policy_dir=REPO_ROOT / "policy",
            committed_out=committed_out,
            version=version,
        )
        self.assertEqual(rc, 0)


class TestProjectSettingsTemplate(unittest.TestCase):
    def test_template_denies_powershell_and_mpr(self):
        commands = json.loads(
            (REPO_ROOT / "policy" / "mxcli-commands.json").read_text(encoding="utf-8")
        )["commands"]
        tpl = b._project_settings_template(commands)
        self.assertIn("PowerShell", tpl["permissions"]["deny"])
        self.assertIn("Edit(**/*.mpr)", tpl["permissions"]["deny"])
        self.assertIn("Write(**/mprcontents/**)", tpl["permissions"]["deny"])
        self.assertTrue(any("mxcli show" in a for a in tpl["permissions"]["allow"]))


if __name__ == "__main__":
    unittest.main()
