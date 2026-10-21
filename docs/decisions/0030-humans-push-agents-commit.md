# ADR-0030: Humans push and open PRs; agents commit locally

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

Pushing and opening a PR publishes work and starts CI and review. That is a
human decision. Agent reports that speculate about push status ("ready to
push", "not pushed yet") add noise and have been wrong.

## Decision

Humans push and open PRs (GitHub Desktop or git). Agents commit locally and
report the commits only. They do not push, merge, or comment on push status.
Recorded in `AGENTS.md` under "How to work here".

## Consequences

- Positive: Nothing leaves the machine without a human choosing to send it.
- Negative: The human must push before CI runs on agent work.

## Versions

Applies regardless of version.

## References

- ADR-0009, ADR-0029.
