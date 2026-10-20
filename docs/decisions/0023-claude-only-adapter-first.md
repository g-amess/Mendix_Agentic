# ADR-0023: Only the Claude Code adapter is built now

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The design (ADR-0001, ADR-0018) supports many adapters, but every active
adapter is maintenance: capability-map updates, build/`--check` runs in
CI, drift reviews. Shipping adapters for tools nobody on the team uses is
code we have to maintain without a user.

## Decision

- Phase 2 ships one adapter only: `adapters/claude/` (Claude Code).
- A new adapter is added when a team adopts that tool and commits to
  maintaining its capability map. Opening a stub adapter "to be ready" is
  not sufficient.

## Consequences

- Positive: Smaller surface area; one adapter to keep green in CI.
- Positive: We can design the Cursor / Aider / Copilot adapter after we
  learn from the Claude one.
- Negative: Someone who wants to use Mendix_Agentic from Cursor on day
  one has to write the adapter themselves (or pick Claude).
- Follow-ups: Document a short "how to add an adapter" guide in phase 3+.

## Versions

Applies regardless of version.

## References

- ADR-0001, ADR-0018, ADR-0022.
