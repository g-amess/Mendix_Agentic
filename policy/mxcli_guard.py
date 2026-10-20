#!/usr/bin/env python3
"""policy/mxcli_guard.py — tool-agnostic policy guard for mxcli invocations.

Two entry modes:

- **Hook mode** (default when stdin is a pipe and no subcommand is given):
  reads a Claude Code `PreToolUse` JSON payload on stdin and emits a JSON
  decision on stdout per
  https://code.claude.com/docs/en/hooks (fields: `hookSpecificOutput.hookEventName`,
  `permissionDecision` ∈ {allow, deny, ask}, `permissionDecisionReason`).
  Exit code is always 0 on a well-formed payload; a `deny` decision is
  carried in the JSON. If the payload cannot be parsed, exit 2 (so Claude
  Code treats stderr as the block reason — see hooks exit-code semantics).

- **CLI mode**: `mxcli_guard.py check --agent <name> -- <command>...`
  returns 0 for allow, 2 for deny. The deny reason goes to stderr. Useful
  from git hooks, CI, or other agent harnesses.

Stdlib only (ADR-0006). Python 3.10+.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HOOK_EVENT = "PreToolUse"
POLICY_DIR = Path(__file__).resolve().parent
REPO_ROOT = POLICY_DIR.parent
LOG_PATH_REL = ".mxagent/guard.log"

# -----------------------------------------------------------------------------
# Decision type
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str
    rule: str  # short identifier of the rule that fired

    def as_hook_json(self) -> str:
        return json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "permissionDecision": "allow" if self.allow else "deny",
                    "permissionDecisionReason": self.reason,
                }
            }
        )


# -----------------------------------------------------------------------------
# Policy data loading
# -----------------------------------------------------------------------------


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_commands(policy_dir: Path = POLICY_DIR) -> dict:
    return _load_json(policy_dir / "mxcli-commands.json").get("commands", {})


def load_ownership(policy_dir: Path = POLICY_DIR) -> dict:
    return _load_json(policy_dir / "ownership.json").get("agents", {})


def load_stop_ops(policy_dir: Path = POLICY_DIR) -> list[dict]:
    return _load_json(policy_dir / "stop-operations.json").get("stop_operations", [])


# -----------------------------------------------------------------------------
# Parsing helpers
# -----------------------------------------------------------------------------

_SHELL_SPLITTERS = re.compile(r"(?:\|\||&&|;|\||&(?!&))")


def _split_shell_segments(command: str) -> list[str]:
    """Split a Bash command on &&, ||, ;, |, & into trimmed segments."""
    return [seg.strip() for seg in _SHELL_SPLITTERS.split(command) if seg.strip()]


def _tokenise(segment: str) -> list[str]:
    """Shell-tokenise with graceful fallback for unbalanced quotes."""
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        try:
            return shlex.split(segment, posix=False)
        except ValueError:
            return segment.split()


@dataclass
class MxcliInvocation:
    subcommand: str | None  # None if we could not identify one
    args: list[str]
    mpr_path: str | None
    inline_script: str | None  # from -c <script>
    exec_script_path: str | None  # from `exec <path>`
    raw_tokens: list[str]


def _parse_mxcli(tokens: list[str]) -> MxcliInvocation | None:
    """Parse a tokenised segment starting with `mxcli` (possibly after env prefixes)."""
    i = 0
    # Allow env var prefixes like FOO=bar BAZ=qux mxcli ...
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    if i >= len(tokens):
        return None
    exe = tokens[i]
    base = os.path.basename(exe)
    # Strip .exe / .cmd / .bat extension
    base_noext = re.sub(r"\.(exe|cmd|bat)$", "", base, flags=re.IGNORECASE)
    if base_noext.lower() != "mxcli":
        return None
    i += 1

    mpr_path: str | None = None
    inline_script: str | None = None
    exec_script_path: str | None = None
    subcommand: str | None = None
    positional: list[str] = []

    # Options that take a value (both --long and -s short forms we care about).
    value_opts = {"-p", "--project", "-c", "--command", "-o", "--output"}

    while i < len(tokens):
        tok = tokens[i]
        if tok == "--":
            positional.extend(tokens[i + 1 :])
            break
        if tok in value_opts and i + 1 < len(tokens):
            val = tokens[i + 1]
            if tok in {"-p", "--project"}:
                mpr_path = val
            elif tok in {"-c", "--command"}:
                inline_script = val
            i += 2
            continue
        m_eq = re.match(r"^(--?[A-Za-z0-9][A-Za-z0-9-]*)=(.*)$", tok)
        if m_eq and m_eq.group(1) in value_opts:
            opt, val = m_eq.group(1), m_eq.group(2)
            if opt in {"-p", "--project"}:
                mpr_path = val
            elif opt in {"-c", "--command"}:
                inline_script = val
            i += 1
            continue
        if tok.startswith("-"):
            # Unknown flag; skip just this token (treat as valueless)
            i += 1
            continue
        positional.append(tok)
        i += 1

    if positional:
        subcommand = positional[0]
        if subcommand == "exec" and len(positional) >= 2:
            exec_script_path = positional[1]

    # If -c is used and no subcommand present, treat as exec of inline MDL
    if subcommand is None and inline_script is not None:
        subcommand = "exec"

    return MxcliInvocation(
        subcommand=subcommand,
        args=positional,
        mpr_path=mpr_path,
        inline_script=inline_script,
        exec_script_path=exec_script_path,
        raw_tokens=tokens,
    )


def extract_mxcli_invocations(command: str) -> list[MxcliInvocation]:
    out: list[MxcliInvocation] = []
    for seg in _split_shell_segments(command):
        toks = _tokenise(seg)
        if not toks:
            continue
        inv = _parse_mxcli(toks)
        if inv is not None:
            out.append(inv)
    return out


# -----------------------------------------------------------------------------
# Environment helpers (lock file, git, stop ops, check cache)
# -----------------------------------------------------------------------------


def _candidate_mpr_dirs(mpr_path: str | None, cwd: Path) -> list[Path]:
    dirs: list[Path] = []
    if mpr_path:
        p = Path(mpr_path)
        if not p.is_absolute():
            p = cwd / p
        if p.suffix.lower() == ".mpr":
            dirs.append(p.parent if p.parent != Path("") else cwd)
        else:
            dirs.append(p)
    dirs.append(cwd)
    return dirs


def studio_pro_lock_present(mpr_path: str | None, cwd: Path) -> str | None:
    """Return the lock-file path if a Studio Pro lock is present, else None.

    Lock-file convention per v0.26.0 cmd_exec.go: `<project>.mpr.lock` beside
    the `.mpr`. We check both an explicit `-p <path>` and any `*.mpr.lock`
    siblings in the candidate directories.
    """
    for d in _candidate_mpr_dirs(mpr_path, cwd):
        if not d.exists():
            continue
        if mpr_path:
            p = Path(mpr_path)
            if not p.is_absolute():
                p = cwd / p
            if p.suffix.lower() == ".mpr":
                lock = p.with_suffix(p.suffix + ".lock")
                if lock.exists():
                    return str(lock)
        for entry in d.iterdir():
            if entry.name.endswith(".mpr.lock") and entry.is_file():
                return str(entry)
    return None


def mpr_has_uncommitted_changes(cwd: Path) -> str | None:
    """Return the first dirty path matching *.mpr or mprcontents/**, else None.

    Falls back to None if git is unavailable; the guard treats absence as
    'cannot verify, do not block on this rule alone'. (Rule 7 is a best-effort
    check — the lock-file rule remains the primary stop.)
    """
    try:
        p = subprocess.run(
            ["git", "-C", str(cwd), "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    for line in p.stdout.splitlines():
        # Format: XY <path>
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if path.endswith(".mpr") or path.startswith("mprcontents/") or "/mprcontents/" in path:
            return path
    return None


def _normalise_mdl(text: str) -> str:
    """Collapse whitespace and upper-case for substring matching."""
    return re.sub(r"\s+", " ", text).upper()


def script_contains_stop_op(script_text: str, stop_ops: list[dict]) -> dict | None:
    norm = _normalise_mdl(script_text)
    for op in stop_ops:
        pat = _normalise_mdl(op.get("pattern", ""))
        if pat and pat in norm:
            return op
    return None


def script_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_passed_for(script_text: str, cwd: Path) -> bool:
    marker = cwd / ".mxagent" / "checks" / f"{script_sha256(script_text)}.ok"
    return marker.exists()


def _read_script_text(inv: MxcliInvocation, cwd: Path) -> str | None:
    if inv.inline_script is not None:
        return inv.inline_script
    if inv.exec_script_path:
        p = Path(inv.exec_script_path)
        if not p.is_absolute():
            p = cwd / p
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


# -----------------------------------------------------------------------------
# Edit/Write path check (rule 2)
# -----------------------------------------------------------------------------

_MPR_PATTERNS = ("*.mpr",)


def _is_mpr_path(path: str) -> bool:
    name = os.path.basename(path.replace("\\", "/"))
    norm = path.replace("\\", "/")
    if any(fnmatch.fnmatchcase(name, pat) for pat in _MPR_PATTERNS):
        return True
    if norm.startswith("mprcontents/") or "/mprcontents/" in norm:
        return True
    return False


def _edit_write_target(tool_name: str, tool_input: dict) -> str | None:
    if tool_name in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        for key in ("file_path", "notebook_path", "path"):
            val = tool_input.get(key)
            if isinstance(val, str) and val:
                return val
    return None


# -----------------------------------------------------------------------------
# Core decision
# -----------------------------------------------------------------------------


def _classify(cmd: str, commands: dict) -> str:
    entry = commands.get(cmd)
    if not entry:
        return "WRITE"  # rule 4
    cls = entry.get("class", "WRITE").upper()
    if cls == "READ" and entry.get("verified") is True:
        return "READ"
    if cls == "READ" and entry.get("verified") is not True:
        # Unverified READ falls back to WRITE per ADR-0007
        return "WRITE"
    if cls == "UNKNOWN":
        return "WRITE"
    return "WRITE"


def decide(
    *,
    tool_name: str,
    tool_input: dict,
    agent: str,
    cwd: Path,
    commands: dict,
    ownership: dict,
    stop_ops: list[dict],
) -> Decision:
    # Rule 2 — Edit/Write on *.mpr or mprcontents/**
    target = _edit_write_target(tool_name, tool_input)
    if target and _is_mpr_path(target):
        return Decision(
            allow=False,
            reason=(
                f"Rule 2: model files are only changed via `mxcli exec`, not direct "
                f"Edit/Write (target: {target}). Draft an MDL script, run `mxcli check`, "
                f"get approval, then `mxcli exec`."
            ),
            rule="R2",
        )

    # Not a bash/mxcli command and not Edit/Write → allow (rule 1)
    if tool_name != "Bash":
        if tool_name in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
            # Target was non-mpr, allow
            return Decision(allow=True, reason="Edit/Write on non-model path", rule="R1")
        return Decision(allow=True, reason="Tool is not Bash/Edit/Write; guard has no opinion", rule="R1")

    command = tool_input.get("command", "")
    if not isinstance(command, str):
        return Decision(allow=True, reason="No command string present; guard has no opinion", rule="R1")

    invocations = extract_mxcli_invocations(command)
    if not invocations:
        return Decision(allow=True, reason="No mxcli invocation detected", rule="R1")

    # If multiple mxcli invocations in the same command, deny on the first that would deny.
    for inv in invocations:
        d = _decide_single(
            inv=inv,
            agent=agent,
            cwd=cwd,
            commands=commands,
            ownership=ownership,
            stop_ops=stop_ops,
        )
        if not d.allow:
            return d
    return Decision(allow=True, reason="All mxcli invocations in command are READ or permitted", rule="R3")


def _decide_single(
    *,
    inv: MxcliInvocation,
    agent: str,
    cwd: Path,
    commands: dict,
    ownership: dict,
    stop_ops: list[dict],
) -> Decision:
    sub = inv.subcommand
    if sub is None:
        return Decision(
            allow=False,
            reason=(
                "Rule 4: could not identify an mxcli subcommand (unknown invocation shape); "
                "treating as WRITE. Rewrite the command with an explicit subcommand."
            ),
            rule="R4",
        )

    cls = _classify(sub, commands)
    entry = commands.get(sub, {})
    verified = bool(entry.get("verified"))

    if cls == "READ":
        return Decision(allow=True, reason=f"mxcli {sub} is READ (verified)", rule="R3")

    # From here on we are treating this as WRITE (rule 4 covers unknown/unverified).
    # Rule 5 — ownership
    owner_entry = ownership.get(agent)
    if not owner_entry or sub not in owner_entry.get("allow", []):
        owners = [name for name, data in ownership.items() if sub in data.get("allow", [])]
        owner_hint = (
            f"Owners of `{sub}`: {', '.join(owners)}." if owners else
            f"No agent currently owns `{sub}` (phase 1 ships ownership.json empty). "
            "Hand this write to a designated writer, or add the agent to policy/ownership.json "
            "via a reviewed change."
        )
        reason_prefix = "Rule 4+5" if not entry or not verified else "Rule 5"
        return Decision(
            allow=False,
            reason=(
                f"{reason_prefix}: `mxcli {sub}` is a WRITE and agent `{agent}` is not "
                f"authorised. {owner_hint}"
            ),
            rule="R5",
        )

    # Rule 6 — Studio Pro lock file present
    lock = studio_pro_lock_present(inv.mpr_path, cwd)
    if lock:
        return Decision(
            allow=False,
            reason=(
                f"Rule 6: Studio Pro has the project open (lock file: {lock}). "
                "Close Studio Pro or use the MCP path. Do not pass `--force` to bypass."
            ),
            rule="R6",
        )

    # Rule 7 — .mpr / mprcontents/ dirty
    dirty = mpr_has_uncommitted_changes(cwd)
    if dirty:
        return Decision(
            allow=False,
            reason=(
                f"Rule 7: `{dirty}` has uncommitted changes. Commit or snapshot the "
                "model before running a WRITE command, so the change is reversible."
            ),
            rule="R7",
        )

    if sub == "exec":
        script_text = _read_script_text(inv, cwd)
        if script_text is None:
            return Decision(
                allow=False,
                reason=(
                    "Rule 8/9: `mxcli exec` was issued but the script could not be read "
                    "(no `-c` and no readable file argument). Pass the script file explicitly."
                ),
                rule="R8",
            )
        # Rule 8 — stop ops
        hit = script_contains_stop_op(script_text, stop_ops)
        if hit:
            return Decision(
                allow=False,
                reason=(
                    f"Rule 8: script contains banned MDL `{hit.get('pattern')}` "
                    f"({hit.get('id')}: {hit.get('reason')}). "
                    "Remove the statement or escalate to a human reviewer."
                ),
                rule="R8",
            )
        # Rule 9 — must have passing check
        if not check_passed_for(script_text, cwd):
            return Decision(
                allow=False,
                reason=(
                    "Rule 9: no recorded passing `mxcli check` for this script. "
                    "Run `mxcli check` first; on success write "
                    f"`.mxagent/checks/{script_sha256(script_text)}.ok` and retry."
                ),
                rule="R9",
            )

    return Decision(
        allow=True,
        reason=f"mxcli {sub} is a WRITE and agent `{agent}` is authorised; preconditions clear.",
        rule="R5",
    )


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------


def log_decision(
    *, mode: str, agent: str, tool_name: str, decision: Decision, extra: dict | None = None
) -> None:
    log_path = REPO_ROOT / LOG_PATH_REL
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "mode": mode,
            "agent": agent,
            "tool": tool_name,
            "allow": decision.allow,
            "rule": decision.rule,
            "reason": decision.reason,
        }
        if extra:
            rec.update(extra)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError:
        pass  # logging must never block a decision


# -----------------------------------------------------------------------------
# Entry points
# -----------------------------------------------------------------------------


def _agent_from_env(default: str = "claude-code") -> str:
    return os.environ.get("MX_AGENT") or default


def run_hook_mode(stdin_text: str, cwd: Path | None = None) -> tuple[str, int]:
    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError as e:
        print(f"mxcli_guard: invalid JSON on stdin ({e})", file=sys.stderr)
        return "", 2
    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    cwd_path = Path(payload.get("cwd") or (cwd or Path.cwd()))
    agent = _agent_from_env()
    commands = load_commands()
    ownership = load_ownership()
    stop_ops = load_stop_ops()
    decision = decide(
        tool_name=tool_name,
        tool_input=tool_input,
        agent=agent,
        cwd=cwd_path,
        commands=commands,
        ownership=ownership,
        stop_ops=stop_ops,
    )
    log_decision(
        mode="hook",
        agent=agent,
        tool_name=tool_name,
        decision=decision,
        extra={"tool_input_preview": _preview(tool_input)},
    )
    return decision.as_hook_json(), 0


def run_cli_check(agent: str, command_tokens: list[str], cwd: Path | None = None) -> tuple[str, int]:
    cwd_path = cwd or Path.cwd()
    # Reconstruct a command string: if tokens look like a single Bash command, join;
    # if the first token is `Edit` or `Write`, treat specially via --tool.
    command = " ".join(shlex.quote(t) for t in command_tokens)
    tool_input = {"command": command}
    commands = load_commands()
    ownership = load_ownership()
    stop_ops = load_stop_ops()
    decision = decide(
        tool_name="Bash",
        tool_input=tool_input,
        agent=agent,
        cwd=cwd_path,
        commands=commands,
        ownership=ownership,
        stop_ops=stop_ops,
    )
    log_decision(mode="cli", agent=agent, tool_name="Bash", decision=decision)
    msg = ("ALLOW: " if decision.allow else "DENY: ") + decision.reason
    return msg, (0 if decision.allow else 2)


def _preview(d: dict, limit: int = 200) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, str) and len(v) > limit:
            out[k] = v[:limit] + "…"
        else:
            out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        # Hook mode on stdin
        stdin_text = sys.stdin.read()
        out, rc = run_hook_mode(stdin_text)
        if out:
            print(out)
        return rc

    ap = argparse.ArgumentParser(description="mxcli policy guard (hook + CLI).")
    sub = ap.add_subparsers(dest="mode", required=True)
    check = sub.add_parser("check", help="Check a command (CLI mode).")
    check.add_argument("--agent", default=_agent_from_env(), help="Calling agent name.")
    check.add_argument("rest", nargs=argparse.REMAINDER, help="-- <command tokens...>")
    args = ap.parse_args(argv)

    if args.mode == "check":
        tokens = args.rest
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        if not tokens:
            print("mxcli_guard check: no command given after --", file=sys.stderr)
            return 2
        msg, rc = run_cli_check(args.agent, tokens)
        stream = sys.stdout if rc == 0 else sys.stderr
        print(msg, file=stream)
        return rc

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
