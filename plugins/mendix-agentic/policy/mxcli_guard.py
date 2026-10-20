#!/usr/bin/env python3
"""policy/mxcli_guard.py — tool-agnostic policy guard for mxcli invocations.

Two entry modes:

- **Hook mode** (default when no subcommand is given): reads a Claude Code
  `PreToolUse` JSON payload on stdin and emits a JSON decision on stdout per
  https://code.claude.com/docs/en/hooks (fields:
  `hookSpecificOutput.hookEventName`, `permissionDecision` ∈ {allow, deny, ask},
  `permissionDecisionReason`). Exit code is 0 on a well-formed payload; a
  `deny` decision is carried in the JSON. If the payload cannot be parsed,
  exit 2 (so Claude Code treats stderr as the block reason per hooks
  exit-code semantics).

- **CLI mode**: `mxcli_guard.py check --agent <name> -- <command>...`
  returns 0 for allow, 2 for deny. The deny reason goes to stderr. Useful
  from git hooks, CI, or other agent harnesses.

Rules, evaluated in order:

- **R0**  Guard raised an exception (fail-closed per ADR-0010) → deny.
- **R1**  Not a shell/edit tool call → allow (guard has no opinion).
- **R2**  Edit/Write/MultiEdit/NotebookEdit on `*.mpr` or `mprcontents/**`
          → deny.
- **R2a** Edit/Write/MultiEdit/NotebookEdit on `.mxagent/**` or `policy/**`
          → deny (guard-state protection, ADR-0010).
- **R2b** Shell command that modifies `.mxagent/**` or `policy/**` → deny.
- **R2c** Shell command setting `MXCLI_ALLOW_STUDIO_PRO_OPEN` or passing
          `--force` / `--no-check` to `mxcli exec` → deny (ADR-0011).
- **R2d** PowerShell command invoking mxcli through a dangerous construct
          (Invoke-Expression, `iex`, `-EncodedCommand`, backtick escapes,
          `$(...)` subexpressions, `&` call operator, `Start-Process`) OR
          a PowerShell+mxcli invocation the parser cannot confidently
          classify → deny (ADR-0016).
- **R3**  Verified READ mxcli command → allow.
- **R4**  Unlisted / unverified mxcli command → treat as WRITE. An
          unlisted CHILD of a listed parent is also WRITE: a child never
          inherits a parent's READ class (ADR-0014).
- **R4-c** Root invocation with `-c "<mdl>"`: every statement must begin
          with a confirmed MDL read verb (SHOW, DESCRIBE, SELECT, OQL)
          per the grammar at the pinned SHA (ADR-0015). Otherwise WRITE.
          Root without `-c` (REPL or stdin) is WRITE unconditionally.
- **R5**  WRITE when the calling agent is not an owner of the command →
          deny, naming the owner.
- **R6**  WRITE when a Studio Pro lock file (`<project>.mpr.lock`) is
          present → deny.
- **R7a** WRITE when git is unavailable or the cwd is not a git working
          tree → deny (fail-closed, ADR-0010).
- **R7**  WRITE when `.mpr` or `mprcontents/**` has uncommitted changes →
          deny. The cache dir `.mxcli/` is ignored by this rule.
- **R8**  `exec <script>` where the script contains a stop-operation → deny.
- **R9**  `exec <script>` without a recorded passing `mxcli check` for the
          script's sha256 → deny.

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
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HOOK_EVENT = "PreToolUse"
POLICY_DIR = Path(__file__).resolve().parent
REPO_ROOT = POLICY_DIR.parent
LOG_PATH_REL = ".mxagent/guard.log"

# Tool-name constants
_SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
_EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})

# -----------------------------------------------------------------------------
# Decision type
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str
    rule: str

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
# Shell parsing helpers
# -----------------------------------------------------------------------------

_SHELL_SPLITTERS = re.compile(r"(?:\|\||&&|;|\||&(?!&))")


def _split_shell_segments(command: str) -> list[str]:
    return [seg.strip() for seg in _SHELL_SPLITTERS.split(command) if seg.strip()]


def _tokenise(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        try:
            return shlex.split(segment, posix=False)
        except ValueError:
            return segment.split()


@dataclass
class MxcliInvocation:
    subcommand: str | None
    args: list[str]
    mpr_path: str | None
    inline_script: str | None
    exec_script_path: str | None
    raw_tokens: list[str]
    flags: list[str]  # all `-foo`/`--foo` tokens from the mxcli invocation


def _parse_mxcli(tokens: list[str]) -> MxcliInvocation | None:
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    if i >= len(tokens):
        return None
    exe = tokens[i]
    base = os.path.basename(exe)
    base_noext = re.sub(r"\.(exe|cmd|bat)$", "", base, flags=re.IGNORECASE)
    if base_noext.lower() != "mxcli":
        return None
    i += 1

    mpr_path: str | None = None
    inline_script: str | None = None
    exec_script_path: str | None = None
    subcommand: str | None = None
    positional: list[str] = []
    flags: list[str] = []

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
            flags.append(tok)
            i += 2
            continue
        m_eq = re.match(r"^(--?[A-Za-z0-9][A-Za-z0-9-]*)=(.*)$", tok)
        if m_eq and m_eq.group(1) in value_opts:
            opt, val = m_eq.group(1), m_eq.group(2)
            if opt in {"-p", "--project"}:
                mpr_path = val
            elif opt in {"-c", "--command"}:
                inline_script = val
            flags.append(opt)
            i += 1
            continue
        if tok.startswith("-"):
            flags.append(tok.split("=", 1)[0])
            i += 1
            continue
        positional.append(tok)
        i += 1

    if positional:
        subcommand = positional[0]
        if subcommand == "exec" and len(positional) >= 2:
            exec_script_path = positional[1]
    # Note: do NOT force subcommand = "exec" when only -c is present. Root
    # `mxcli -c "<mdl>"` is classified by the MDL verbs in the inline script
    # (rule R4-c), not forced to exec.

    return MxcliInvocation(
        subcommand=subcommand,
        args=positional,
        mpr_path=mpr_path,
        inline_script=inline_script,
        exec_script_path=exec_script_path,
        raw_tokens=tokens,
        flags=flags,
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
# Protected-path detection (rules R2a, R2b)
# -----------------------------------------------------------------------------

_MPR_RE = re.compile(r"(?:^|[\\/])mprcontents[\\/]", re.IGNORECASE)
_PROTECTED_PATH_RE = re.compile(
    r"(?:(?:^|[\s\"'=/\\])(?:\.mxagent|policy)(?:[/\\]|\s|$|\"|'))",
    re.IGNORECASE,
)
_MUTATING_VERBS = re.compile(
    r"(?i)(?<![A-Za-z0-9_-])("
    r"rm|del|erase|mv|cp|move|copy|rmdir|rd|"
    r"Remove-Item|Move-Item|Copy-Item|"
    r"Set-Content|Add-Content|Out-File|Clear-Content|New-Item|"
    r"tee"
    r")(?![A-Za-z0-9_-])"
)
_REDIR_INTO_PROTECTED = re.compile(
    r">>?\s*[\"']?\S*(?:\.mxagent|policy)[/\\]", re.IGNORECASE
)


def _is_mpr_path(path: str) -> bool:
    norm = path.replace("\\", "/")
    name = os.path.basename(norm)
    if fnmatch.fnmatchcase(name, "*.mpr"):
        return True
    if norm.startswith("mprcontents/") or "/mprcontents/" in norm:
        return True
    return False


def _is_protected_state_path(path: str) -> bool:
    norm = path.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    if norm.startswith(".mxagent/") or "/.mxagent/" in "/" + norm:
        return True
    if norm.startswith("policy/") or "/policy/" in "/" + norm:
        return True
    if norm in {".mxagent", "policy"}:
        return True
    return False


def _shell_modifies_protected(command: str) -> str | None:
    """Return the matching segment if the shell command modifies .mxagent/ or policy/."""
    if _REDIR_INTO_PROTECTED.search(command):
        return "redirection into a protected path"
    for seg in _split_shell_segments(command):
        if _PROTECTED_PATH_RE.search(seg) and _MUTATING_VERBS.search(seg):
            return seg[:120]
    return None


# -----------------------------------------------------------------------------
# Override detection (rule R2c)
# -----------------------------------------------------------------------------

_OVERRIDE_ENV_RE = re.compile(r"MXCLI_ALLOW_STUDIO_PRO_OPEN", re.IGNORECASE)
_FORBIDDEN_EXEC_FLAGS = {"--force", "-f", "--no-check"}


# -----------------------------------------------------------------------------
# MDL read-verb allowlist (rule R4-c, ADR-0015)
# -----------------------------------------------------------------------------
#
# Confirmed from the MDL grammar at
# https://github.com/mendixlabs/mxcli/blob/v0.26.0/mdl/grammar/MDLParser.g4#L931-L936
# where `dqlStatement` ::= showStatement | describeStatement | catalogSelectQuery | oqlQuery.
# EXPLAIN is NOT in the grammar at this tag and is deliberately omitted.
_MDL_READ_VERBS = frozenset({"SHOW", "DESCRIBE", "SELECT", "OQL"})


def _classify_inline_mdl(script_text: str) -> str:
    """Return "READ" if every non-empty statement starts with a read verb; else "WRITE".

    Comments and whitespace are stripped. Semicolons split statements.
    """
    # Strip /* … */ and // … line comments
    stripped = re.sub(r"/\*.*?\*/", " ", script_text, flags=re.DOTALL)
    stripped = re.sub(r"//[^\n]*", " ", stripped)
    statements = [s.strip() for s in stripped.split(";")]
    non_empty = [s for s in statements if s]
    if not non_empty:
        return "WRITE"
    for stmt in non_empty:
        first = stmt.split(None, 1)[0].upper() if stmt.split() else ""
        if first not in _MDL_READ_VERBS:
            return "WRITE"
    return "READ"


# -----------------------------------------------------------------------------
# PowerShell dangerous constructs (rule R2d, ADR-0016)
# -----------------------------------------------------------------------------

_POWERSHELL_DANGER_RE = re.compile(
    r"(?i)("
    r"\bInvoke-Expression\b|"
    r"\biex\b|"
    r"(?<!\w)-EncodedCommand(?!\w)|"
    r"(?<!\w)-enc(?!\w)|"
    r"\bStart-Process\b|"
    r"\$\(|"           # subexpression $(...)
    r"`"               # backtick escape (PowerShell line/char escape)
    r")"
)


def _powershell_has_danger(command: str) -> str | None:
    m = _POWERSHELL_DANGER_RE.search(command)
    if m:
        return m.group(0)
    # The call operator '&' is handled separately so we don't match '&&' (bash and-chain)
    # or '&' used as a background operator by Claude Code tool's rendering.
    # A PowerShell call-operator pattern is `& <path>` with a space; distinguish from `&&`.
    if re.search(r"(?<![&])&\s+[A-Za-z0-9_./\\\"']", command) and "mxcli" in command.lower():
        return "& (call operator)"
    return None


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
            dirs.append(p.parent if str(p.parent) else cwd)
        else:
            dirs.append(p)
    dirs.append(cwd)
    return dirs


def studio_pro_lock_present(mpr_path: str | None, cwd: Path) -> str | None:
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
        try:
            for entry in d.iterdir():
                if entry.name.endswith(".mpr.lock") and entry.is_file():
                    return str(entry)
        except OSError:
            continue
    return None


def _run_git(args: list[str], cwd: Path, timeout: int = 5) -> tuple[int, str]:
    env = os.environ.copy()
    # Constrain git's upward walk so a test temp dir inside a user profile that
    # happens to sit under a parent repo cannot cross into it.
    ceiling = env.get("MXAGENT_GIT_CEILING")
    if ceiling:
        env["GIT_CEILING_DIRECTORIES"] = ceiling
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""


def _git_available() -> bool:
    return shutil.which("git") is not None


def _is_git_worktree(cwd: Path) -> bool:
    if not _git_available():
        return False
    rc, out = _run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    return rc == 0 and out.lower() == "true"


def mpr_has_uncommitted_changes(cwd: Path) -> str | None:
    rc, out = _run_git(["status", "--porcelain"], cwd)
    if rc != 0:
        return None
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if path.endswith(".mpr") or path.startswith("mprcontents/") or "/mprcontents/" in path:
            return path
    return None


def _normalise_mdl(text: str) -> str:
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
# Edit/Write path extraction (rules R2 and R2a)
# -----------------------------------------------------------------------------


def _edit_write_target(tool_name: str, tool_input: dict) -> str | None:
    if tool_name in _EDIT_TOOLS:
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
        return "WRITE"
    cls = str(entry.get("class", "WRITE")).upper()
    if cls == "READ" and entry.get("verified") is True:
        return "READ"
    return "WRITE"


def _lookup_subcommand(positional: list[str], commands: dict) -> str | None:
    """Return the longest matching key in `commands`, trying depth 3→2→1.

    If `positional` has 2+ tokens and no deeper key matches, and the top-level
    token is a known PARENT (any other key starts with "<top> "), return
    None — signalling an unlisted child, which must be classified as WRITE
    regardless of the parent's class (ADR-0014).
    """
    if not positional:
        return ""
    # Try depth 3, then 2.
    for depth in (3, 2):
        if len(positional) >= depth:
            key = " ".join(positional[:depth])
            if key in commands:
                return key
    # No deeper key matched. If positional has 2+ tokens AND the top-level
    # is a known PARENT (any other key starts with "<top> "), the child is
    # unlisted → None (forces WRITE per ADR-0014).
    top = positional[0]
    if len(positional) >= 2:
        prefix = top + " "
        if any(k.startswith(prefix) for k in commands):
            return None
    # Leaf command (or single-token invocation): fall back to depth-1 lookup.
    return top


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
    # R2 / R2a — Edit-family tools on protected paths
    target = _edit_write_target(tool_name, tool_input)
    if target:
        if _is_mpr_path(target):
            return Decision(
                allow=False,
                reason=(
                    f"Rule 2: model files are only changed via `mxcli exec`, not "
                    f"direct Edit/Write (target: {target}). Draft an MDL script, run "
                    f"`mxcli check`, get approval, then `mxcli exec`."
                ),
                rule="R2",
            )
        if _is_protected_state_path(target):
            return Decision(
                allow=False,
                reason=(
                    f"Rule 2a: `{target}` is protected guard state "
                    f"(`.mxagent/**` and `policy/**`). Change these through a "
                    f"reviewed git commit on the main branch, not from an agent "
                    f"tool call."
                ),
                rule="R2a",
            )

    # R1 — not a shell tool and not an edit tool → allow
    if tool_name not in _SHELL_TOOLS:
        if tool_name in _EDIT_TOOLS:
            return Decision(allow=True, reason="Edit/Write on non-protected path", rule="R1")
        return Decision(
            allow=True,
            reason=f"Tool `{tool_name}` is not shell/edit; guard has no opinion",
            rule="R1",
        )

    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        return Decision(
            allow=True,
            reason="No command string present; guard has no opinion",
            rule="R1",
        )

    # R2b — shell command modifies .mxagent/** or policy/**
    hit = _shell_modifies_protected(command)
    if hit:
        return Decision(
            allow=False,
            reason=(
                f"Rule 2b: shell command appears to modify protected guard state "
                f"(`.mxagent/**` or `policy/**`): `{hit}`. Guard state changes go "
                f"through a reviewed git commit, not an agent tool call."
            ),
            rule="R2b",
        )

    # R2c — command tries to set MXCLI_ALLOW_STUDIO_PRO_OPEN
    if _OVERRIDE_ENV_RE.search(command):
        return Decision(
            allow=False,
            reason=(
                "Rule 2c: `MXCLI_ALLOW_STUDIO_PRO_OPEN` disables the Studio Pro "
                "lock-file check in mxcli; agents may never set it. Close Studio "
                "Pro, or escalate to a human reviewer who can run the command."
            ),
            rule="R2c",
        )

    # R2d — PowerShell backstop: a dangerous construct that reaches mxcli,
    # or a PowerShell+mxcli command we cannot confidently parse, is denied.
    if tool_name == "PowerShell" and "mxcli" in command.lower():
        danger = _powershell_has_danger(command)
        if danger:
            return Decision(
                allow=False,
                reason=(
                    f"Rule 2d: PowerShell command uses `{danger}` to invoke mxcli. "
                    "Use the Bash tool (Git Bash on Windows) for mxcli; the guard's "
                    "PowerShell parsing is a backstop, not a supported shell "
                    "(ADR-0016)."
                ),
                rule="R2d",
            )

    invocations = extract_mxcli_invocations(command)
    if not invocations:
        if tool_name == "PowerShell" and "mxcli" in command.lower():
            return Decision(
                allow=False,
                reason=(
                    "Rule 2d: PowerShell command mentions `mxcli` but the guard "
                    "could not identify an mxcli invocation. Use the Bash tool for "
                    "mxcli (ADR-0016)."
                ),
                rule="R2d",
            )
        return Decision(allow=True, reason="No mxcli invocation detected", rule="R1")

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
    return Decision(
        allow=True,
        reason="All mxcli invocations in command are READ or permitted",
        rule="R3",
    )


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
    # Root invocation: no subcommand. Classify by inline -c MDL (rule R4-c),
    # or treat REPL/stdin forms as WRITE.
    if sub is None:
        if inv.inline_script is None:
            return Decision(
                allow=False,
                reason=(
                    "Rule 4-c: `mxcli` with no subcommand and no `-c` is a REPL or "
                    "stdin invocation (write-capable). The guard cannot see the "
                    "statements that will run. Pass `-c \"<mdl>\"` or use `exec` "
                    "with a reviewed script file (ADR-0015)."
                ),
                rule="R4-c",
            )
        inline_cls = _classify_inline_mdl(inv.inline_script)
        if inline_cls == "READ":
            return Decision(
                allow=True,
                reason=(
                    "Rule 4-c: `-c` script contains only MDL read verbs (SHOW, "
                    "DESCRIBE, SELECT, OQL) per the pinned grammar."
                ),
                rule="R3",
            )
        # Treat the inline MDL as an exec script for stop-op / check-marker rules.
        sub = "exec"
        inv.subcommand = "exec"

    # Prefer two-token key (e.g. "auth status") over bare parent ("auth").
    lookup = _lookup_subcommand(inv.args, commands) if sub != "exec" else "exec"
    if lookup is None:
        # Unlisted child of a known parent — force WRITE (ADR-0014).
        return Decision(
            allow=False,
            reason=(
                f"Rule 4: `mxcli {sub} {inv.args[1] if len(inv.args) > 1 else ''}` is "
                f"not a listed subcommand of the known parent `{sub}`. Unlisted "
                f"children are WRITE and may never inherit the parent's READ class "
                f"(ADR-0014). Add an entry to policy/mxcli-commands.json via a "
                f"reviewed change if this is a legitimate command."
            ),
            rule="R4",
        )
    cls = _classify(lookup, commands)
    entry = commands.get(lookup, {})
    verified = bool(entry.get("verified"))

    if cls == "READ":
        return Decision(allow=True, reason=f"mxcli {lookup} is READ (verified)", rule="R3")

    # R5 — ownership
    owner_entry = ownership.get(agent)
    if not owner_entry or sub not in owner_entry.get("allow", []):
        owners = [name for name, data in ownership.items() if sub in data.get("allow", [])]
        owner_hint = (
            f"Owners of `{sub}`: {', '.join(owners)}." if owners else
            f"No agent currently owns `{sub}` (phase 1 ships ownership.json empty). "
            "Hand this write to a designated writer, or add the agent to "
            "policy/ownership.json via a reviewed change."
        )
        reason_prefix = "Rule 4+5" if not entry or not verified else "Rule 5"
        return Decision(
            allow=False,
            reason=(
                f"{reason_prefix}: `mxcli {sub}` is a WRITE and agent `{agent}` is "
                f"not authorised. {owner_hint}"
            ),
            rule="R5",
        )

    # R2c (again, at mxcli flag granularity) — exec with --force or --no-check
    if sub == "exec":
        forbidden = sorted(set(inv.flags) & _FORBIDDEN_EXEC_FLAGS)
        if forbidden:
            return Decision(
                allow=False,
                reason=(
                    f"Rule 2c: `mxcli exec {' '.join(forbidden)}` bypasses mxcli's "
                    "own safety checks (Studio Pro lock, pre-exec validation). "
                    "Agents may never pass these flags. Remove them and let mxcli "
                    "run its checks, or escalate to a human reviewer."
                ),
                rule="R2c",
            )

    # R6 — Studio Pro lock
    lock = studio_pro_lock_present(inv.mpr_path, cwd)
    if lock:
        return Decision(
            allow=False,
            reason=(
                f"Rule 6: Studio Pro has the project open (lock file: {lock}). "
                "Close Studio Pro and retry. Do not use `--force` or set "
                "`MXCLI_ALLOW_STUDIO_PRO_OPEN`."
            ),
            rule="R6",
        )

    # R7a — fail closed: WRITE requires git and a git worktree
    if not _git_available():
        return Decision(
            allow=False,
            reason=(
                "Rule 7a: git is not available on PATH. Install git — the guard "
                "needs it to confirm the model is committed before a WRITE."
            ),
            rule="R7a",
        )
    if not _is_git_worktree(cwd):
        return Decision(
            allow=False,
            reason=(
                f"Rule 7a: `{cwd}` is not inside a git working tree. Agents may "
                f"only WRITE from a git-tracked project so the change is "
                f"reversible. Run `git init` and commit the project, or move to a "
                f"tracked clone."
            ),
            rule="R7a",
        )

    # R7 — dirty mpr
    dirty = mpr_has_uncommitted_changes(cwd)
    if dirty:
        return Decision(
            allow=False,
            reason=(
                f"Rule 7: `{dirty}` has uncommitted changes. Commit or snapshot "
                f"the model before running a WRITE command so the change is "
                f"reversible."
            ),
            rule="R7",
        )

    if sub == "exec":
        script_text = _read_script_text(inv, cwd)
        if script_text is None:
            return Decision(
                allow=False,
                reason=(
                    "Rule 8/9: `mxcli exec` was issued but the script could not be "
                    "read (no `-c` and no readable file argument). Pass the script "
                    "file explicitly."
                ),
                rule="R8",
            )
        hit = script_contains_stop_op(script_text, stop_ops)
        if hit:
            return Decision(
                allow=False,
                reason=(
                    f"Rule 8: script contains banned MDL `{hit.get('pattern')}` "
                    f"({hit.get('id')}: {hit.get('reason')}). Remove the statement "
                    f"or escalate to a human reviewer."
                ),
                rule="R8",
            )
        if not check_passed_for(script_text, cwd):
            return Decision(
                allow=False,
                reason=(
                    "Rule 9: no recorded passing `mxcli check` for this script. Run "
                    "`mxcli check` first; on success write "
                    f"`.mxagent/checks/{script_sha256(script_text)}.ok` and retry."
                ),
                rule="R9",
            )

    return Decision(
        allow=True,
        reason=f"mxcli {sub} is a WRITE and agent `{agent}` is authorised; preconditions clear.",
        rule="R5",
    )


def decide_safe(**kwargs) -> Decision:
    """Fail-closed wrapper (R0, ADR-0010): any exception in decide → deny."""
    try:
        return decide(**kwargs)
    except Exception as e:  # noqa: BLE001 — explicitly fail-closed
        return Decision(
            allow=False,
            reason=(
                f"Rule 0: guard raised {type(e).__name__}: {e}. Fail-closed per "
                f"ADR-0010. Fix the guard or the policy data; do not retry."
            ),
            rule="R0",
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
        pass


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
    try:
        commands = load_commands()
        ownership = load_ownership()
        stop_ops = load_stop_ops()
    except Exception as e:
        decision = Decision(
            allow=False,
            reason=f"Rule 0: policy data unreadable ({type(e).__name__}: {e}). Fail-closed per ADR-0010.",
            rule="R0",
        )
    else:
        decision = decide_safe(
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
    command = " ".join(shlex.quote(t) for t in command_tokens)
    tool_input = {"command": command}
    try:
        commands = load_commands()
        ownership = load_ownership()
        stop_ops = load_stop_ops()
    except Exception as e:
        decision = Decision(
            allow=False,
            reason=f"Rule 0: policy data unreadable ({type(e).__name__}: {e}). Fail-closed per ADR-0010.",
            rule="R0",
        )
    else:
        decision = decide_safe(
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
