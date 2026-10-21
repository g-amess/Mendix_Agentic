"""Tests for adapters/claude/build.py.

Covers:
- Capability mapping (role capabilities → Claude Code tools).
- Model-tier mapping (fast/standard/deep → haiku/sonnet/opus).
- Ownership generation (ADR-0019).
- Skill sidecar fields emitted top-level (ADR-0027), golden.
- Subagent `tools:` as a comma-separated string (ADR-0028), golden.
- Fail-closed hook command (ADR-0026).
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
HUB_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "core" / "hub_two_spokes"


def _build_into_tmp(core_dir: Path = FIXTURE) -> Path:
    """Build a fixture into a temp dir. build() also rewrites the repo's
    policy/ownership.json and project-settings template, so restore them."""
    tmp = Path(tempfile.mkdtemp(prefix="mxagent-build-"))
    side_outputs = (REPO_ROOT / "policy" / "ownership.json", b.PROJECT_SETTINGS_OUT)
    saved = {p: p.read_bytes() for p in side_outputs if p.exists()}
    try:
        b.build(
            core_dir=core_dir,
            policy_dir=REPO_ROOT / "policy",
            out_root=tmp / "mendix-agentic",
            version="test-0.0.0",
        )
    finally:
        for p, data in saved.items():
            p.write_bytes(data)
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
        cmd = pre["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", cmd)
        self.assertEqual(cmd.split()[0], "python")
        # ADR-0026: any non-zero exit becomes a blocking exit 2.
        self.assertTrue(
            cmd.endswith(
                "|| { echo 'mendix-agentic guard could not run — run bin/doctor' >&2; exit 2; }"
            ),
            msg=cmd,
        )

    def test_plugin_readme_generated(self):
        readme = (self.plugin / "README.md").read_text(encoding="utf-8")
        self.assertIn("GENERATED", readme)
        self.assertIn("never hand-edit", readme)

    def test_plugin_display_name(self):
        pj = json.loads((self.plugin / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(pj["displayName"], "Mendix Agentic")

    def test_agent_tools_mapped(self):
        txt = (self.plugin / "agents" / "orchestrator.md").read_text()
        fm = parse_frontmatter(txt, filename="orchestrator.md").data
        # orchestrator has capabilities: read-files, search-files,
        # edit-artefacts, mxcli-read, delegate, ask-human
        # → tools: Read, Grep, Glob, Edit, Write, MultiEdit, Bash,
        #          AskUserQuestion, Agent(analyst,writer)
        tools = fm["tools"]
        self.assertIsInstance(tools, str)  # ADR-0028: never a YAML list
        self.assertEqual(
            tools,
            "Read, Grep, Glob, Edit, Write, MultiEdit, Bash, AskUserQuestion, "
            "Agent(mendix-agentic:analyst, mendix-agentic:writer)",
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

    def test_skill_claude_fields_top_level_golden(self):
        """ADR-0027: sidecar fields are top-level; metadata stays as in core."""
        md = (self.plugin / "skills" / "mdl-draft" / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = md.split("\n---\n", 1)[0] + "\n---\n"
        self.assertEqual(
            frontmatter,
            "---\n"
            "name: mdl-draft\n"
            'description: "Draft an MDL script that effects the requested model change. '
            'Use when the writer needs an input script before running `mxcli check`."\n'
            "license: Apache-2.0\n"
            'compatibility: "Requires mxcli v0.26.0 or later"\n'
            "metadata:\n"
            "  tier: core\n"
            "disable-model-invocation: true\n"
            "user-invocable: true\n"
            "allowed-tools:\n"
            "  - Read\n"
            "  - Grep\n"
            "  - Glob\n"
            '  - "Bash(mxcli:*)"\n'
            "---\n",
        )
        fm = parse_frontmatter(md, filename="SKILL.md").data
        self.assertIs(fm["disable-model-invocation"], True)
        self.assertNotIn("claude", fm["metadata"])

    def test_core_skill_stays_spec_only(self):
        core_md = (FIXTURE / "skills" / "mdl-draft" / "SKILL.md").read_text(encoding="utf-8")
        fm = parse_frontmatter(core_md, filename="SKILL.md").data
        for key in b.CLAUDE_SKILL_FIELDS:
            self.assertNotIn(key, fm)

    def test_policy_copied(self):
        self.assertTrue((self.plugin / "policy" / "mxcli_guard.py").exists())
        self.assertTrue((self.plugin / "policy" / "mxcli-commands.json").exists())
        self.assertTrue((self.plugin / "policy" / "stop-operations.json").exists())


class TestHubToolsGolden(unittest.TestCase):
    """ADR-0028: the hub delegating to two spokes emits one comma-separated
    string, in capability-map order, with the spokes namespaced."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = _build_into_tmp(HUB_FIXTURE)
        cls.plugin = cls.tmp / "mendix-agentic"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_hub_tools_line(self):
        text = (self.plugin / "agents" / "hub.md").read_text(encoding="utf-8")
        self.assertIn(
            "\ntools: Read, Grep, Glob, "
            "Agent(mendix-agentic:spoke-a, mendix-agentic:spoke-b)\n",
            text,
        )
        self.assertNotIn("tools: [", text)
        fm = parse_frontmatter(text, filename="hub.md").data
        self.assertEqual(
            fm["tools"],
            "Read, Grep, Glob, Agent(mendix-agentic:spoke-a, mendix-agentic:spoke-b)",
        )

    def test_spoke_tools_line(self):
        text = (self.plugin / "agents" / "spoke-a.md").read_text(encoding="utf-8")
        self.assertIn("\ntools: Read\n", text)


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


class TestDeterminism(unittest.TestCase):
    """ADR-0031: two builds into different temp dirs produce identical bytes
    and never contain absolute paths, usernames, or timestamps."""

    def test_two_builds_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as c:
            a_out = Path(a) / "mendix-agentic"
            c_out = Path(c) / "mendix-agentic"
            b.build(
                core_dir=REPO_ROOT / "core",
                policy_dir=REPO_ROOT / "policy",
                out_root=a_out,
                version="test-0.0.0",
            )
            b.build(
                core_dir=REPO_ROOT / "core",
                policy_dir=REPO_ROOT / "policy",
                out_root=c_out,
                version="test-0.0.0",
            )
            diffs = b._dir_diff(a_out, c_out)
            self.assertEqual(diffs, [], msg=f"determinism broken: {diffs}")

    def test_no_absolute_paths_or_usernames_in_output(self):
        import datetime
        import getpass
        import re
        import socket
        marker_user = getpass.getuser()
        hostname = socket.gethostname()
        year = str(datetime.date.today().year)
        with tempfile.TemporaryDirectory() as a:
            a_out = Path(a) / "mendix-agentic"
            b.build(
                core_dir=REPO_ROOT / "core",
                policy_dir=REPO_ROOT / "policy",
                out_root=a_out,
                version="test-0.0.0",
            )
            workspace = str(REPO_ROOT).encode("utf-8")
            for rel in b._list_files(a_out):
                content = b._read_bytes_lf(a_out / rel)
                self.assertNotIn(
                    marker_user.encode("utf-8"), content,
                    msg=f"{rel} contains the local username",
                )
                self.assertNotIn(
                    workspace, content,
                    msg=f"{rel} contains the local workspace path",
                )
                if hostname:
                    self.assertNotIn(
                        hostname.lower().encode("utf-8"), content.lower(),
                        msg=f"{rel} contains the hostname",
                    )
                # The current year as a standalone number (a date stamp);
                # digits inside longer tokens such as SHA-256s don't count.
                self.assertIsNone(
                    re.search(rb"(?<![0-9A-Za-z])" + year.encode() + rb"(?![0-9A-Za-z])", content),
                    msg=f"{rel} contains the current year {year}",
                )

    def test_no_empty_directories(self):
        with tempfile.TemporaryDirectory() as a:
            a_out = Path(a) / "mendix-agentic"
            b.build(
                core_dir=REPO_ROOT / "core",
                policy_dir=REPO_ROOT / "policy",
                out_root=a_out,
                version="test-0.0.0",
            )
            for p in a_out.rglob("*"):
                if p.is_dir():
                    self.assertTrue(
                        any(p.iterdir()),
                        msg=f"empty directory in build output: {p.relative_to(a_out)}",
                    )


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
