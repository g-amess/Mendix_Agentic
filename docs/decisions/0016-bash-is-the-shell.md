# ADR-0016: Bash is the supported agent shell; PowerShell is a backstop

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

Claude Code exposes both a `Bash` tool (POSIX shell, Git Bash on Windows)
and a `PowerShell` tool. Our guard parses commands with POSIX `shlex`.
PowerShell syntax (`$env:FOO`, backtick line continuations, `&` call
operator, `$(…)` subexpressions, `-EncodedCommand <base64>`) is not
POSIX-shaped; a cleanly-written malicious PowerShell line can be hard to
parse. We also do not need PowerShell for anything we actually do — mxcli
runs identically from Bash on Windows.

## Decision

- **Bash is the supported agent shell for this repo.** Phase 2+ adapter-
  generated `.claude/settings.json` will **deny** the PowerShell tool to
  agents, defaulting them to Bash (Git Bash on Windows).
- The guard still handles PowerShell as a **backstop** so that a poorly-
  configured host or a user override is not an immediate escape:
  - **Rule R2d**: a PowerShell command that mentions mxcli AND contains a
    dangerous construct (`Invoke-Expression`, `iex`, `-EncodedCommand`,
    `-enc`, `Start-Process`, backtick escape, `$(…)` subexpression, `&`
    call operator) → **deny** with "use the Bash tool for mxcli".
  - **Rule R2d (unclassifiable)**: a PowerShell command that mentions
    mxcli but from which the parser cannot extract an invocation → **deny**
    for the same reason.

## Consequences

- Positive: One supported shell, one set of parsing assumptions, one
  smaller attack surface.
- Positive: Agents that reach for the "harder" PowerShell paths are told
  to use Bash and told why.
- Negative: Occasionally a legitimate Windows-only task (COM, registry,
  AD) needs PowerShell. That still exits the agent sandbox; the human
  runs it. Phase 2+ can revisit if real demand appears.
- Follow-ups: Ship the `.claude/settings.json` deny-PowerShell entry with
  the Claude Code adapter in phase 2.

## Versions

- mxcli: any
- Claude Code: current PreToolUse schema, which handles both Bash and
  PowerShell as separate `tool_name`s.

## References

- ADR-0005, ADR-0010.
- `policy/mxcli_guard.py` — rule R2d, `_powershell_has_danger`.
