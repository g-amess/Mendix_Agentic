# ADR-0025: The Claude Code minimum version is pinned and enforced by doctor

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

The plugin relies on Claude Code features that arrived at different times:
native `AGENTS.md` reading, the `Agent(...)` allowlist for main-thread agents,
plugin hooks, `omitClaudeMd`, and background subagents. Phase 2 was built and
checked on 2.1.128, which predates several of them, and `displayName` in
`plugin.json` was rejected there. A contributor on an old CLI gets a plugin
that loads but behaves differently from the one we tested, with no error.

## Decision

`docs/version-matrix.md` records a Claude Code minimum (2.1.281) with the
changelog entry for every feature that sets it, and the version we tested on.
`bin/doctor` reports FAIL below the minimum, with the fix "run
`claude update`; in VS Code also update the extension and restart". Generated
plugin output is validated with `claude plugin validate` on the minimum
version as well as the tested version.

## Consequences

- Positive: A too-old CLI fails loudly at doctor time instead of quietly at
  run time.
- Positive: `displayName` can be emitted again (accepted on 2.1.281 and
  2.1.305).
- Negative: Raising the minimum is a deliberate change: update the matrix,
  `MIN_CLAUDE_CODE` in `bin/doctor.py`, and re-run the validation.
- Follow-ups: Re-check the minimum when the plugin starts relying on a new
  Claude Code feature.

## Versions

- mxcli: any
- Studio Pro: any
- Mendix runtime: any
- Python: 3.10+
- Claude Code: ≥ 2.1.281 (tested 2.1.305)

## References

- `docs/version-matrix.md` (feature → changelog entry table).
- github.com/anthropics/claude-code/blob/main/CHANGELOG.md.
- ADR-0022 (plugin), ADR-0026 (hook).
