# ADR-0026: Hook commands turn any guard failure into a blocking exit code

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

ADR-0010 makes the guard fail closed, but only once the guard is running.
Claude Code blocks a tool call only when a PreToolUse hook exits 2 (or
returns a deny decision); any other non-zero exit is a non-blocking error and
the call proceeds. If `python` is missing (bash exit 127) or an exception
escapes the guard (Python exit 1), the tool call ran unguarded. We confirmed
this on Claude Code 2.1.305: with an unwrapped hook pointing at a missing
interpreter, a Bash call went ahead.

Plugin hook commands run under bash on every platform; on Windows that is
Git Bash (`$0=/usr/bin/bash`, `%ComSpec%` unexpanded). So POSIX shell syntax
is safe in the command.

## Decision

The generated hook command is

    python "${CLAUDE_PLUGIN_ROOT}/policy/mxcli_guard.py" || { echo 'mendix-agentic guard could not run — run bin/doctor' >&2; exit 2; }

Any non-zero exit becomes exit 2 with that message on stderr, after
whatever the guard itself wrote. The interpreter is `python`, not `py -3`:
`py` exists only on Windows, and the same command must work on Linux and
macOS. `bin/doctor` checks that `python` resolves to Python ≥ 3.10.

## Consequences

- Positive: A broken environment blocks guarded tools instead of letting
  them through. The message tells the user what to run.
- Negative: A missing `python` blocks every Bash, PowerShell, Edit and Write
  call until it is fixed. That is the intended trade-off.
- Follow-ups: If Claude Code ever runs plugin hooks under a non-POSIX shell,
  this command must change; `docs/install.md` records how to re-test.

## Versions

- Python: 3.10+
- Claude Code: tested on 2.1.305 (minimum 2.1.281, ADR-0025)
- Others: any

## References

- ADR-0010 (guard fails closed), ADR-0016 (bash is the shell).
- `docs/install.md` — "Fail-closed hook: evidence".
- code.claude.com/docs/en/hooks (exit-code semantics).
