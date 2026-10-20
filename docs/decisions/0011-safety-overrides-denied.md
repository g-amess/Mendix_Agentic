# ADR-0011: mxcli safety overrides are denied by the guard

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

mxcli exposes several escape hatches that disable its own safety checks:

- `mxcli exec --force` — bypasses the Studio Pro lock-file check.
- `mxcli exec --no-check` — skips the pre-exec MDL validation.
- `MXCLI_ALLOW_STUDIO_PRO_OPEN=1` — globally disables the lock-file check.

These exist for human operators in genuine emergencies. An agent reaching
for them is, by definition, trying to do something the author of mxcli
decided should not happen without conscious consent.

## Decision

The guard **denies** any shell command that:

- passes `--force` or `--no-check` to `mxcli exec`, or
- sets `MXCLI_ALLOW_STUDIO_PRO_OPEN` in any form (inline `VAR=1`, `export`,
  `env`, PowerShell `$env:…`, cmd `set`), or
- includes the string `MXCLI_ALLOW_STUDIO_PRO_OPEN` anywhere in the command.

`bin/doctor` additionally FAILs if the variable is already set in the
calling shell, so a contributor knows before any agent runs.

Agents that genuinely need to bypass a safety check must escalate to a
human reviewer; the human runs the command outside the agent.

## Consequences

- Positive: Removes the easiest footguns.
- Positive: `bin/doctor` surfaces an already-poisoned environment early.
- Negative: An agent trying to work around a stale lock file is blocked;
  that is the intended outcome.
- Follow-ups: If upstream adds further overrides, extend the deny list in
  `policy/mxcli_guard.py` and update this ADR.

## Versions

- mxcli: v0.26.0 (overrides observed in `cmd_exec.go` at this tag).

## References

- ADR-0004, ADR-0005.
- Rules R2c and R5a in `policy/mxcli_guard.py`.
