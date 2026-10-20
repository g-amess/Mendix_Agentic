"""Unit tests for policy/mxcli_guard.py.

Each rule has at least one dedicated test, plus coverage for Windows paths,
quoted arguments, chained commands, `-c` inline MDL, unknown subcommands,
and malformed inputs.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from policy import mxcli_guard as g  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "hooks"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def mk_decide(**overrides):
    """Call g.decide with sensible defaults; allow per-test overrides."""
    base = dict(
        tool_name="Bash",
        tool_input={},
        agent="claude-code",
        cwd=Path.cwd(),
        commands=g.load_commands(),
        ownership=g.load_ownership(),
        stop_ops=g.load_stop_ops(),
    )
    base.update(overrides)
    return g.decide(**base)


class TestParseMxcli(unittest.TestCase):
    def test_simple_show(self):
        invs = g.extract_mxcli_invocations("mxcli show modules")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].subcommand, "show")

    def test_dash_p_and_dash_c(self):
        invs = g.extract_mxcli_invocations('mxcli -p app.mpr -c "SHOW modules"')
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].mpr_path, "app.mpr")
        self.assertEqual(invs[0].inline_script, "SHOW modules")
        self.assertEqual(invs[0].subcommand, "exec")  # -c implies exec

    def test_chained_command(self):
        invs = g.extract_mxcli_invocations("echo hi && mxcli -p app.mpr exec m.mdl")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].subcommand, "exec")
        self.assertEqual(invs[0].exec_script_path, "m.mdl")

    def test_pipe_chain(self):
        invs = g.extract_mxcli_invocations("mxcli show modules | wc -l")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].subcommand, "show")

    def test_not_mxcli(self):
        self.assertEqual(g.extract_mxcli_invocations("ls -la"), [])

    def test_env_prefix(self):
        invs = g.extract_mxcli_invocations("MX_AGENT=writer mxcli show modules")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].subcommand, "show")

    def test_mxcli_with_exe_suffix(self):
        invs = g.extract_mxcli_invocations("mxcli.exe show modules")
        self.assertEqual(len(invs), 1)

    def test_absolute_path_to_mxcli(self):
        invs = g.extract_mxcli_invocations("/usr/local/bin/mxcli show modules")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].subcommand, "show")


class TestRule1_Noop(unittest.TestCase):
    """Not an mxcli command and not Edit/Write → allow."""

    def test_bash_unrelated(self):
        d = mk_decide(tool_name="Bash", tool_input={"command": "ls -la"})
        self.assertTrue(d.allow)
        self.assertEqual(d.rule, "R1")

    def test_tool_read(self):
        d = mk_decide(tool_name="Read", tool_input={"file_path": "x.py"})
        self.assertTrue(d.allow)


class TestRule2_EditMpr(unittest.TestCase):
    """Edit/Write targeting *.mpr or mprcontents/** → deny."""

    def test_edit_mpr(self):
        d = mk_decide(tool_name="Edit", tool_input={"file_path": "app.mpr"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2")

    def test_write_mprcontents(self):
        d = mk_decide(
            tool_name="Write",
            tool_input={"file_path": "mprcontents/Entities/MyEntity.yaml", "content": "x"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2")

    def test_windows_path(self):
        d = mk_decide(
            tool_name="Edit", tool_input={"file_path": r"C:\projects\mxapp\app.mpr"}
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2")

    def test_edit_non_model(self):
        d = mk_decide(tool_name="Edit", tool_input={"file_path": "README.md"})
        self.assertTrue(d.allow)


class TestRule3_ReadMxcli(unittest.TestCase):
    """mxcli READ command → allow."""

    def test_show(self):
        d = mk_decide(tool_input={"command": "mxcli show modules"})
        self.assertTrue(d.allow)
        self.assertEqual(d.rule, "R3")

    def test_check(self):
        d = mk_decide(tool_input={"command": "mxcli check -p app.mpr script.mdl"})
        self.assertTrue(d.allow)


class TestRule4_Unknown(unittest.TestCase):
    """Unlisted mxcli command → treat as WRITE (and therefore deny by rule 5)."""

    def test_unknown_subcommand(self):
        d = mk_decide(tool_input={"command": "mxcli brand-new-subcommand"})
        self.assertFalse(d.allow)
        self.assertIn("WRITE", d.reason)
        self.assertEqual(d.rule, "R5")


class TestRule5_Ownership(unittest.TestCase):
    """WRITE without ownership → deny, naming the owner (or lack thereof)."""

    def test_exec_denied_phase1(self):
        d = mk_decide(tool_input={"command": "mxcli -p app.mpr exec m.mdl"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")
        self.assertIn("not authorised", d.reason)

    def test_writer_allowed_when_registered(self):
        ownership = {"writer": {"allow": ["exec"], "description": "test writer"}}
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "m.mdl"
            script.write_text("SHOW modules;\n", encoding="utf-8")
            # Pre-record the passing check marker so rule 9 does not block.
            marker_dir = Path(td) / ".mxagent" / "checks"
            marker_dir.mkdir(parents=True)
            (marker_dir / f"{g.script_sha256(script.read_text())}.ok").write_text("ok")
            d = mk_decide(
                agent="writer",
                tool_input={"command": f"mxcli exec {script.name}"},
                cwd=Path(td),
                ownership=ownership,
            )
        self.assertTrue(d.allow, msg=d.reason)


class TestRule6_StudioProLock(unittest.TestCase):
    def test_lock_present(self):
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "app.mpr").write_text("fake", encoding="utf-8")
            (tdp / "app.mpr.lock").write_text("lock", encoding="utf-8")
            script = tdp / "m.mdl"
            script.write_text("SHOW modules;\n", encoding="utf-8")
            marker_dir = tdp / ".mxagent" / "checks"
            marker_dir.mkdir(parents=True)
            (marker_dir / f"{g.script_sha256(script.read_text())}.ok").write_text("ok")
            d = mk_decide(
                agent="writer",
                tool_input={"command": f"mxcli -p app.mpr exec {script}"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R6")


class TestRule7_DirtyMpr(unittest.TestCase):
    def test_dirty_mpr_blocks(self):
        """Rule 7 is best-effort: run inside a real git repo with dirty .mpr."""
        import subprocess

        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            subprocess.run(
                ["git", "init", "-q", "-b", "main", str(tdp)], check=True
            )
            subprocess.run(
                ["git", "-C", str(tdp), "config", "user.email", "t@t"], check=True
            )
            subprocess.run(
                ["git", "-C", str(tdp), "config", "user.name", "t"], check=True
            )
            (tdp / "app.mpr").write_text("v1", encoding="utf-8")
            subprocess.run(["git", "-C", str(tdp), "add", "app.mpr"], check=True)
            subprocess.run(
                ["git", "-C", str(tdp), "commit", "-q", "-m", "add mpr"], check=True
            )
            (tdp / "app.mpr").write_text("v2 dirty", encoding="utf-8")  # dirty
            script = tdp / "m.mdl"
            script.write_text("SHOW modules;\n", encoding="utf-8")
            marker_dir = tdp / ".mxagent" / "checks"
            marker_dir.mkdir(parents=True)
            (marker_dir / f"{g.script_sha256(script.read_text())}.ok").write_text("ok")
            d = mk_decide(
                agent="writer",
                tool_input={"command": f"mxcli exec {script.name}"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow, msg=d.reason)
        self.assertEqual(d.rule, "R7")


class TestRule8_StopOperations(unittest.TestCase):
    def test_alter_settings_blocked(self):
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            script = tdp / "m.mdl"
            script.write_text("alter   settings foo = 1;\n", encoding="utf-8")
            # Even with a passing check marker, stop-op must still deny
            marker_dir = tdp / ".mxagent" / "checks"
            marker_dir.mkdir(parents=True)
            (marker_dir / f"{g.script_sha256(script.read_text())}.ok").write_text("ok")
            d = mk_decide(
                agent="writer",
                tool_input={"command": f"mxcli exec {script.name}"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R8")


class TestRule9_CheckRequired(unittest.TestCase):
    def test_missing_check_marker(self):
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            script = tdp / "m.mdl"
            script.write_text("SHOW modules;\n", encoding="utf-8")
            d = mk_decide(
                agent="writer",
                tool_input={"command": f"mxcli exec {script.name}"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R9")


class TestEdgeCases(unittest.TestCase):
    def test_chained_mxcli_exec_detected(self):
        d = mk_decide(
            tool_input={"command": "echo starting && mxcli -p app.mpr exec m.mdl"}
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")

    def test_quoted_args(self):
        d = mk_decide(
            tool_input={"command": 'mxcli -p "spaced path/app.mpr" -c "SHOW modules"'}
        )
        # -c implies exec → WRITE → denied in phase 1 (no writer)
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")

    def test_unknown_agent_type_denied_on_write(self):
        d = mk_decide(
            agent="unknown-agent",
            tool_input={"command": "mxcli -p app.mpr exec m.mdl"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")

    def test_missing_fields_hook_payload(self):
        """Hook mode: a payload missing tool_name/tool_input must not crash."""
        payload = {"hook_event_name": "PreToolUse"}
        out, rc = g.run_hook_mode(json.dumps(payload))
        self.assertEqual(rc, 0)
        parsed = json.loads(out)
        # Missing tool defaults to '' which is treated as "not Bash/Edit/Write" → allow
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_hook_mode_invalid_json(self):
        out, rc = g.run_hook_mode("not json")
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")

    def test_hook_mode_fixture_show_allows(self):
        payload = load_fixture("bash_mxcli_show.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        self.assertEqual(rc, 0)
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_hook_mode_fixture_exec_denies(self):
        payload = load_fixture("bash_mxcli_exec.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        self.assertEqual(rc, 0)
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_edit_mpr_denies(self):
        payload = load_fixture("edit_mpr.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        self.assertEqual(rc, 0)
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_write_mprcontents_denies(self):
        payload = load_fixture("write_mprcontents.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_bash_unrelated_allows(self):
        payload = load_fixture("bash_unrelated.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "allow"
        )

    def test_hook_mode_fixture_dash_c_denies(self):
        payload = load_fixture("bash_mxcli_dash_c.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        # -c with SHOW is still "exec" subcommand → WRITE → deny in phase 1
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_chained_exec_denies(self):
        payload = load_fixture("bash_chained_mxcli_exec.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_unknown_mxcli_denies(self):
        payload = load_fixture("bash_unknown_mxcli.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_windows_edit_denies(self):
        payload = load_fixture("windows_edit_mpr.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_hook_mode_fixture_missing_fields_allows(self):
        payload = load_fixture("missing_fields.json")
        out, rc = g.run_hook_mode(json.dumps(payload))
        self.assertEqual(rc, 0)
        parsed = json.loads(out)
        self.assertEqual(
            parsed["hookSpecificOutput"]["permissionDecision"], "allow"
        )


class TestCliMode(unittest.TestCase):
    def test_cli_check_allow_show(self):
        msg, rc = g.run_cli_check("claude-code", ["mxcli", "show", "modules"])
        self.assertEqual(rc, 0)
        self.assertTrue(msg.startswith("ALLOW"))

    def test_cli_check_deny_exec(self):
        msg, rc = g.run_cli_check(
            "claude-code", ["mxcli", "-p", "app.mpr", "exec", "m.mdl"]
        )
        self.assertEqual(rc, 2)
        self.assertTrue(msg.startswith("DENY"))


class TestClassify(unittest.TestCase):
    def test_unverified_read_falls_back_to_write(self):
        commands = {
            "foo": {"class": "READ", "verified": False, "source": "x"},
        }
        self.assertEqual(g._classify("foo", commands), "WRITE")

    def test_verified_read_is_read(self):
        commands = {
            "foo": {"class": "READ", "verified": True, "source": "x"},
        }
        self.assertEqual(g._classify("foo", commands), "READ")

    def test_unknown_class_is_write(self):
        commands = {"foo": {"class": "UNKNOWN", "verified": True}}
        self.assertEqual(g._classify("foo", commands), "WRITE")

    def test_absent_is_write(self):
        self.assertEqual(g._classify("not-there", {}), "WRITE")


if __name__ == "__main__":
    unittest.main()
