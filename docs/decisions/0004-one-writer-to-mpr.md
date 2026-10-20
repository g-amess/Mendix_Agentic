# ADR-0004: One writer to the `.mpr` at a time

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

A Mendix `.mpr` is a SQLite database. Concurrent writers race, corrupt the
file, or produce "last write wins" surprises that bypass review. Studio Pro
takes a lock when open; mxcli must respect it.

## Decision

At any moment, **at most one agent may write to the `.mpr`**. That agent is
the designated writer (phase 3+). Parallelism is allowed only for **read-only
analysis and review** (`SHOW`, `DESCRIBE`, `search`, `callers`, `callees`,
`refs`, `impact`, `lint`, `report`). The writer must run `SHOW → draft →
mxcli check → human approval → mxcli exec` in that order.

## Consequences

- Positive: Deterministic, auditable model changes.
- Positive: Studio Pro and mxcli coexist safely.
- Negative: Throughput capped on model edits; mitigate by batching MDL into
  one `exec` per approved draft.
- Follow-ups: `policy/ownership.json` names the writer per repo (phase 3+).

## Versions

- mxcli: ≥ v0.26.0 (target). Earlier versions UNVERIFIED.
- Studio Pro: 11.12 LTS+ (target).
- Mendix runtime: any.
- Python: any.
- Claude Code: any.

## References

- `AGENTS.md` non-negotiables 3 and 4.
- ADR-0003.
