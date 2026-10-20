"""Unit tests for policy/mxcli_guard.py.

Each rule has at least one dedicated test, plus coverage for Windows paths,
quoted arguments, chained commands, `-c` inline MDL, unknown subcommands,
PowerShell, override-flag denies, protected-state writes, and fail-closed
behaviour.
"""
from __future__ import annotations

import json
import os
import subprocess
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


def _mk_git_repo(path: Path, add_mpr: bool = False, dirty_mpr: bool = False) -> None:
    """Initialise a git repo at `path` with optional committed/dirty `.mpr`."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    if add_mpr:
        (path / "app.mpr").write_text("v1", encoding="utf-8")
        subprocess.run(["git", "-C", str(path), "add", "app.mpr"], check=True)
        subprocess.run(
            ["git", "-C", str(path), "commit", "-q", "-m", "add mpr"], check=True
        )
        if dirty_mpr:
            (path / "app.mpr").write_text("v2 dirty", encoding="utf-8")
    else:
        # Need an initial commit so `git status` works consistently
        (path / "README.md").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
        subprocess.run(
            ["git", "-C", str(path), "commit", "-q", "-m", "init"], check=True
        )


def mk_decide(**overrides):
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
        self.assertEqual(invs[0].subcommand, "exec")

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

    def test_flags_captured(self):
        invs = g.extract_mxcli_invocations("mxcli exec --force --no-check m.mdl")
        self.assertEqual(len(invs), 1)
        self.assertIn("--force", invs[0].flags)
        self.assertIn("--no-check", invs[0].flags)


class TestRule1_Noop(unittest.TestCase):
    def test_bash_unrelated(self):
        d = mk_decide(tool_name="Bash", tool_input={"command": "ls -la"})
        self.assertTrue(d.allow)
        self.assertEqual(d.rule, "R1")

    def test_tool_read(self):
        d = mk_decide(tool_name="Read", tool_input={"file_path": "x.py"})
        self.assertTrue(d.allow)


class TestRule2_EditMpr(unittest.TestCase):
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


class TestRule2a_ProtectedState(unittest.TestCase):
    def test_edit_policy(self):
        d = mk_decide(
            tool_name="Edit",
            tool_input={"file_path": "policy/mxcli-commands.json"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2a")

    def test_write_mxagent(self):
        d = mk_decide(
            tool_name="Write",
            tool_input={"file_path": ".mxagent/checks/x.ok", "content": "ok"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2a")

    def test_multiedit_policy(self):
        d = mk_decide(
            tool_name="MultiEdit",
            tool_input={"file_path": "policy/ownership.json"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2a")

    def test_notebook_edit_mxagent(self):
        d = mk_decide(
            tool_name="NotebookEdit",
            tool_input={"notebook_path": ".mxagent/notes.ipynb"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2a")


class TestRule2b_ShellWritesProtected(unittest.TestCase):
    def test_rm_mxagent(self):
        d = mk_decide(tool_input={"command": "rm -rf .mxagent/checks"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2b")

    def test_redirect_to_policy(self):
        d = mk_decide(tool_input={"command": "echo x > policy/mxcli-commands.json"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2b")

    def test_powershell_remove_item_mxagent(self):
        d = mk_decide(
            tool_name="PowerShell",
            tool_input={"command": "Remove-Item -Recurse .mxagent/checks"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2b")

    def test_powershell_set_content_policy(self):
        d = mk_decide(
            tool_name="PowerShell",
            tool_input={"command": "Set-Content policy/ownership.json '{}'"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2b")

    def test_ls_policy_allows(self):
        """Reading policy/ is fine; mutating is not."""
        d = mk_decide(tool_input={"command": "ls policy/"})
        self.assertTrue(d.allow)


class TestRule2c_Overrides(unittest.TestCase):
    def test_env_override_inline(self):
        d = mk_decide(
            tool_input={
                "command": "MXCLI_ALLOW_STUDIO_PRO_OPEN=1 mxcli exec m.mdl"
            }
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")

    def test_env_override_export(self):
        d = mk_decide(
            tool_input={
                "command": "export MXCLI_ALLOW_STUDIO_PRO_OPEN=1 && mxcli exec m.mdl"
            }
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")

    def test_env_override_env_prefix(self):
        d = mk_decide(
            tool_input={
                "command": "env MXCLI_ALLOW_STUDIO_PRO_OPEN=1 mxcli exec m.mdl"
            }
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")

    def test_env_override_powershell(self):
        d = mk_decide(
            tool_name="PowerShell",
            tool_input={
                "command": "$env:MXCLI_ALLOW_STUDIO_PRO_OPEN = '1'; mxcli exec m.mdl"
            },
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")

    def test_env_override_cmd_set(self):
        d = mk_decide(
            tool_input={
                "command": "set MXCLI_ALLOW_STUDIO_PRO_OPEN=1 & mxcli exec m.mdl"
            }
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")

    def test_exec_force_denied(self):
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            d = mk_decide(
                agent="writer",
                tool_input={"command": "mxcli exec --force m.mdl"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")

    def test_exec_no_check_denied(self):
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            d = mk_decide(
                agent="writer",
                tool_input={"command": "mxcli exec --no-check m.mdl"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R2c")


class TestRule3_ReadMxcli(unittest.TestCase):
    def test_show(self):
        d = mk_decide(tool_input={"command": "mxcli show modules"})
        self.assertTrue(d.allow)
        self.assertEqual(d.rule, "R3")

    def test_check(self):
        d = mk_decide(tool_input={"command": "mxcli check -p app.mpr script.mdl"})
        self.assertTrue(d.allow)


class TestRule4_Unknown(unittest.TestCase):
    def test_unknown_subcommand(self):
        d = mk_decide(tool_input={"command": "mxcli brand-new-subcommand"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")


class TestRule5_Ownership(unittest.TestCase):
    def test_exec_denied_phase1(self):
        d = mk_decide(tool_input={"command": "mxcli -p app.mpr exec m.mdl"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")
        self.assertIn("not authorised", d.reason)

    def test_writer_allowed_when_registered(self):
        ownership = {"writer": {"allow": ["exec"], "description": "test writer"}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            _mk_git_repo(tdp)
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
                tool_input={"command": f"mxcli -p app.mpr exec {script.name}"},
                cwd=tdp,
                ownership=ownership,
            )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R6")


class TestRule7a_FailClosed(unittest.TestCase):
    def test_write_denied_outside_git_repo(self):
        from unittest import mock
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            script = tdp / "m.mdl"
            script.write_text("SHOW modules;\n", encoding="utf-8")
            marker_dir = tdp / ".mxagent" / "checks"
            marker_dir.mkdir(parents=True)
            (marker_dir / f"{g.script_sha256(script.read_text())}.ok").write_text("ok")
            with mock.patch.object(g, "_is_git_worktree", return_value=False):
                d = mk_decide(
                    agent="writer",
                    tool_input={"command": f"mxcli exec {script.name}"},
                    cwd=tdp,
                    ownership=ownership,
                )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R7a")

    def test_write_denied_when_git_unavailable(self):
        from unittest import mock
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            script = tdp / "m.mdl"
            script.write_text("SHOW modules;\n", encoding="utf-8")
            marker_dir = tdp / ".mxagent" / "checks"
            marker_dir.mkdir(parents=True)
            (marker_dir / f"{g.script_sha256(script.read_text())}.ok").write_text("ok")
            with mock.patch.object(g, "_git_available", return_value=False):
                d = mk_decide(
                    agent="writer",
                    tool_input={"command": f"mxcli exec {script.name}"},
                    cwd=tdp,
                    ownership=ownership,
                )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R7a")


class TestRule7_DirtyMpr(unittest.TestCase):
    def test_dirty_mpr_blocks(self):
        ownership = {"writer": {"allow": ["exec"], "description": ""}}
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            _mk_git_repo(tdp, add_mpr=True, dirty_mpr=True)
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
            _mk_git_repo(tdp)
            script = tdp / "m.mdl"
            script.write_text("alter   settings foo = 1;\n", encoding="utf-8")
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
            _mk_git_repo(tdp)
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


class TestPowerShell(unittest.TestCase):
    def test_powershell_show_allows(self):
        d = mk_decide(
            tool_name="PowerShell",
            tool_input={"command": "mxcli show modules"},
        )
        self.assertTrue(d.allow, msg=d.reason)
        self.assertEqual(d.rule, "R3")

    def test_powershell_exec_denied(self):
        d = mk_decide(
            tool_name="PowerShell",
            tool_input={"command": "mxcli -p app.mpr exec m.mdl"},
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")

    def test_powershell_chained_exec_denied(self):
        d = mk_decide(
            tool_name="PowerShell",
            tool_input={
                "command": "Write-Host hi; mxcli -p app.mpr exec m.mdl"
            },
        )
        self.assertFalse(d.allow)


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
        payload = {"hook_event_name": "PreToolUse"}
        out, rc = g.run_hook_mode(json.dumps(payload))
        self.assertEqual(rc, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_hook_mode_invalid_json(self):
        out, rc = g.run_hook_mode("not json")
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")

    def test_hook_mode_fixture_show_allows(self):
        payload = load_fixture("bash_mxcli_show.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_hook_mode_fixture_exec_denies(self):
        payload = load_fixture("bash_mxcli_exec.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_edit_mpr_denies(self):
        payload = load_fixture("edit_mpr.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_write_mprcontents_denies(self):
        payload = load_fixture("write_mprcontents.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_bash_unrelated_allows(self):
        payload = load_fixture("bash_unrelated.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_hook_mode_fixture_dash_c_denies(self):
        payload = load_fixture("bash_mxcli_dash_c.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_chained_exec_denies(self):
        payload = load_fixture("bash_chained_mxcli_exec.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_unknown_mxcli_denies(self):
        payload = load_fixture("bash_unknown_mxcli.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_windows_edit_denies(self):
        payload = load_fixture("windows_edit_mpr.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_missing_fields_allows(self):
        payload = load_fixture("missing_fields.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_hook_mode_fixture_powershell_show_allows(self):
        payload = load_fixture("powershell_mxcli_show.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_hook_mode_fixture_powershell_exec_denies(self):
        payload = load_fixture("powershell_mxcli_exec.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_override_env_denies(self):
        payload = load_fixture("bash_env_override.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_force_flag_denies(self):
        payload = load_fixture("bash_exec_force.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hook_mode_fixture_protected_write_denies(self):
        payload = load_fixture("edit_policy.json")
        out, _ = g.run_hook_mode(json.dumps(payload))
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_decide_safe_catches_exception(self):
        """Fail-closed wrapper returns deny on exception (ADR-0010)."""
        # Pass a malformed commands dict that will trip classify or iteration
        d = g.decide_safe(
            tool_name="Bash",
            tool_input={"command": "mxcli show modules"},
            agent="x",
            cwd=Path.cwd(),
            commands=None,  # type: ignore[arg-type]
            ownership={},
            stop_ops=[],
        )
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R0")


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


class TestTwoTokenLookup(unittest.TestCase):
    """The guard prefers a 'parent child' key over the bare 'parent' entry."""

    def test_auth_status_read(self):
        d = mk_decide(tool_input={"command": "mxcli auth status"})
        self.assertTrue(d.allow, msg=d.reason)
        self.assertEqual(d.rule, "R3")

    def test_auth_login_still_write(self):
        d = mk_decide(tool_input={"command": "mxcli auth login"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")

    def test_docker_check_read(self):
        d = mk_decide(tool_input={"command": "mxcli docker check"})
        self.assertTrue(d.allow, msg=d.reason)

    def test_docker_build_write(self):
        d = mk_decide(tool_input={"command": "mxcli docker build"})
        self.assertFalse(d.allow)
        self.assertEqual(d.rule, "R5")

    def test_marketplace_search_read(self):
        d = mk_decide(tool_input={"command": "mxcli marketplace search foo"})
        self.assertTrue(d.allow, msg=d.reason)


class TestClassify(unittest.TestCase):
    def test_unverified_read_falls_back_to_write(self):
        commands = {"foo": {"class": "READ", "verified": False, "source": "x"}}
        self.assertEqual(g._classify("foo", commands), "WRITE")

    def test_verified_read_is_read(self):
        commands = {"foo": {"class": "READ", "verified": True, "source": "x"}}
        self.assertEqual(g._classify("foo", commands), "READ")

    def test_unknown_class_is_write(self):
        commands = {"foo": {"class": "UNKNOWN", "verified": True}}
        self.assertEqual(g._classify("foo", commands), "WRITE")

    def test_absent_is_write(self):
        self.assertEqual(g._classify("not-there", {}), "WRITE")


class TestInventoryConsistency(unittest.TestCase):
    """policy/mxcli-commands.json and docs/research/mxcli-inventory.md must agree,
    and no unverified row may be effectively allowed as READ."""

    COMMANDS_JSON = REPO_ROOT / "policy" / "mxcli-commands.json"
    INVENTORY_MD = REPO_ROOT / "docs" / "research" / "mxcli-inventory.md"

    def test_commands_schema(self):
        with open(self.COMMANDS_JSON, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn("commands", data)
        for name, row in data["commands"].items():
            self.assertIn("class", row, f"{name!r} missing class")
            self.assertIn("verified", row, f"{name!r} missing verified")
            self.assertIn("source", row, f"{name!r} missing source")
            self.assertIn(row["class"], {"READ", "WRITE"}, f"{name!r} bad class")

    def test_no_unverified_read_is_actually_read(self):
        """ADR-0007: every effective classification resolves to WRITE if
        unverified, regardless of the declared class."""
        with open(self.COMMANDS_JSON, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for name, row in data["commands"].items():
            effective = g._classify(name, data["commands"])
            if row.get("verified") is not True:
                self.assertEqual(
                    effective,
                    "WRITE",
                    msg=f"{name!r} unverified but effective class is {effective}",
                )

    def test_inventory_mentions_every_command(self):
        """Every command in the JSON must be mentioned in the inventory markdown.

        A command is "mentioned" if its name appears inside a backtick-quoted
        token, optionally followed by placeholder arguments (e.g.
        `` `brain capture <text>` `` matches the key `brain capture`), OR
        as an unquoted table cell. Built-in cobra `help` is exempt — it
        has no dedicated inventory section.
        """
        import re as _re
        EXEMPT = {"help"}
        with open(self.COMMANDS_JSON, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        with open(self.INVENTORY_MD, "r", encoding="utf-8") as fh:
            inventory = fh.read()
        missing: list[str] = []
        for name in data["commands"]:
            if name in EXEMPT:
                continue
            escaped = _re.escape(name)
            patterns = [
                rf"`{escaped}`",       # exact
                rf"`{escaped} ",       # trailing args in same backticks
                rf"`{escaped}\s+<",    # trailing placeholder <arg>
                rf"\|\s+{escaped}\s",  # bare in table cell
            ]
            if not any(_re.search(p, inventory) for p in patterns):
                missing.append(name)
        self.assertEqual(
            missing, [], msg=f"Inventory does not mention: {missing}"
        )


if __name__ == "__main__":
    unittest.main()
