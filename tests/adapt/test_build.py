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
import os
import re
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


def _path_forms(path: str) -> set[bytes]:
    """Native, forward-slash and JSON-escaped (doubled backslash) spellings
    of a path, also for its resolved form (e.g. a Windows 8.3 temp path)."""
    forms: set[bytes] = set()
    for p in {path, os.path.realpath(path)}:
        p = p.rstrip("\\/")
        for f in (p, p.replace("\\", "/"), p.replace("\\", "\\\\")):
            forms.add(f.lower().encode("utf-8"))
    return forms


def _machine_leaks(
    content: bytes, *, repo: str, home: str, tmp: str, user: str, host: str
) -> list[str]:
    """Machine-specific strings in `content`. A username or hostname is only
    a leak as a path segment or a whole token; bare words such as `runner`
    (the GitHub runner's user) occur legitimately in the inventory."""
    leaks: list[str] = []
    low = content.lower()
    for label, path in (("repo path", repo), ("home dir", home), ("temp dir", tmp)):
        for form in _path_forms(path):
            if form in low:
                leaks.append(f"{label} {form.decode()!r}")
    if user:
        u = re.escape(user.encode("utf-8"))
        sep = rb"(?:\\\\|\\|/)"
        for pattern in (
            rb"/home/" + u + rb"/",
            rb"/users/" + u + rb"/",
            rb"[a-z]:" + sep + rb"users" + sep + u + sep,
        ):
            if re.search(pattern, content, re.IGNORECASE):
                leaks.append(f"username path segment {pattern!r}")
    if host and len(host) >= 6:
        if re.search(rb"\b" + re.escape(host.encode("utf-8")) + rb"\b", content, re.IGNORECASE):
            leaks.append(f"hostname {host!r}")
    return leaks


def _this_machine() -> dict[str, str]:
    import getpass
    import socket
    return {
        "repo": str(REPO_ROOT),
        "home": os.path.expanduser("~"),
        "tmp": tempfile.gettempdir(),
        "user": getpass.getuser(),
        "host": socket.gethostname(),
    }


def _scan_for_leaks(out_dir: Path, **machine: str) -> list[str]:
    found: list[str] = []
    for rel in sorted(b._list_files(out_dir)):
        for leak in _machine_leaks(b._read_bytes_lf(out_dir / rel), **machine):
            found.append(f"{rel}: {leak}")
    return found


class TestLeakCheck(unittest.TestCase):
    """Controls for the determinism leak check: it must catch real leaks and
    must not flag ordinary words that happen to equal the username."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="mxagent-leak-"))
        cls.clean = cls.tmp / "clean"
        b.build(
            core_dir=REPO_ROOT / "core",
            policy_dir=REPO_ROOT / "policy",
            out_root=cls.clean,
            version="test-0.0.0",
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _inject(self, text: str) -> Path:
        dest = Path(tempfile.mkdtemp(dir=self.tmp)) / "out"
        shutil.copytree(self.clean, dest)
        target = dest / "policy" / "mxcli-commands.json"
        target.write_bytes(target.read_bytes() + text.encode("utf-8"))
        return dest

    def _assert_caught(self, text: str, **machine: str):
        ids = {**_this_machine(), **machine}
        found = _scan_for_leaks(self._inject(text), **ids)
        self.assertTrue(found, msg=f"leak not caught: {text!r}")

    def test_home_path_caught(self):
        home = os.path.expanduser("~")
        for form in (home, home.replace("\\", "/"), home.replace("\\", "\\\\")):
            self._assert_caught(f'"x": "{form}/notes"')

    def test_repo_path_caught(self):
        repo = str(REPO_ROOT)
        for form in (repo, repo.replace("\\", "/"), repo.replace("\\", "\\\\")):
            self._assert_caught(f"see {form}/policy")

    def test_temp_path_caught(self):
        tmp = tempfile.gettempdir()
        for form in (tmp, tmp.replace("\\", "/"), tmp.replace("\\", "\\\\")):
            self._assert_caught(f"built in {form}/x")

    def test_windows_user_segment_caught(self):
        for text in (
            "C:\\Users\\runner\\x",        # native
            '"C:\\\\Users\\\\runner\\\\x"',  # JSON-escaped
            "d:/users/RUNNER/x",           # other drive, forward slash, case
        ):
            self._assert_caught(text, user="runner", home="/nonexistent-home")

    def test_posix_user_segments_caught(self):
        for text in ("/home/runner/work", "/Users/runner/Library"):
            self._assert_caught(text, user="runner", home="/nonexistent-home")

    def test_hostname_whole_token_caught(self):
        self._assert_caught("built on buildbox-42 today", host="buildbox-42")

    def test_common_word_username_not_flagged(self):
        """CI's user is `runner`; the inventory says 'OQL query runner'."""
        out = self._inject("an OQL query runner")
        ids = {**_this_machine(), "user": "runner"}
        self.assertEqual(_scan_for_leaks(out, **ids), [])

    def test_hostname_inside_word_not_flagged(self):
        out = self._inject("buildboxes and prebuildbox")
        ids = {**_this_machine(), "host": "buildbox"}
        self.assertEqual(_scan_for_leaks(out, **ids), [])

    def test_short_hostname_skipped(self):
        out = self._inject("my box")
        ids = {**_this_machine(), "host": "box"}
        self.assertEqual(_scan_for_leaks(out, **ids), [])


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
        import re
        year = str(datetime.date.today().year)
        with tempfile.TemporaryDirectory() as a:
            a_out = Path(a) / "mendix-agentic"
            b.build(
                core_dir=REPO_ROOT / "core",
                policy_dir=REPO_ROOT / "policy",
                out_root=a_out,
                version="test-0.0.0",
            )
            self.assertEqual(_scan_for_leaks(a_out, **_this_machine()), [])
            for rel in b._list_files(a_out):
                content = b._read_bytes_lf(a_out / rel)
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
