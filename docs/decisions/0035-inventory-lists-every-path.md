# ADR-0035: The inventory lists every command path explicitly

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

ADR-0014 makes an unlisted child of a listed parent WRITE in the guard. Phase
1 relied on that and left out WRITE children of WRITE parents (`docker
build`, `setup mxbuild`, …), on the reasoning that the guard would deny them
anyway. That turned the guard's fallback into an inventory shortcut. The CI
tree check then reported 34 paths "missing", which hid real gaps among
expected ones. Reviewers also could not see each path's source line or side
effects.

The hand-written §2 tables in `docs/research/mxcli-inventory.md` and
`policy/mxcli-commands.json` also drifted apart: the markdown listed paths
the JSON did not.

## Decision

- `policy/mxcli-commands.json` has one row for every command path the
  released binary exposes, including WRITE children of WRITE parents. Each
  row has `class`, `verified`, `source` (file:line permalink at the pinned
  SHA, or "cobra built-in"), and `side_effects`.
- The parent fallback (ADR-0014) stays, but only as a guard safety net for
  paths a newer mxcli adds. It is never a reason to omit a row.
- The JSON is the source of record. The §2 tables in the inventory markdown
  are generated from it by `.github/scripts/render_mxcli_inventory.py`, and
  a unit test fails on drift.

## Consequences

- Positive: The CI tree check is exact; any difference is news.
- Positive: One place to edit; the markdown cannot drift.
- Negative: More rows to maintain on an mxcli upgrade (158 at v0.26.0).

## Versions

- mxcli: v0.26.0 (pinned, ADR-0013)
- Others: any

## References

- ADR-0007, ADR-0014, ADR-0024, ADR-0036.
- `docs/research/mxcli-inventory.md` §8.1.
