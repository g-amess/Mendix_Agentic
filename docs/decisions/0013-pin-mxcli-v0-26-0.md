# ADR-0013: mxcli is pinned at v0.26.0

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

mxcli is young and moves fast. v0.26.0 (released 2026-10-11) is the newest
version we have fully inventoried and tested against. v0.27.0 (2026-10-15)
exists but has not been through the inventory process.

If the policy data (`policy/mxcli-commands.json`) and the installed mxcli
version drift, the guard either denies safe commands or allows new unsafe
ones.

## Decision

- The target version is **mxcli v0.26.0**.
- `docs/version-matrix.md` records v0.26.0 as the tested target.
- Any upgrade requires:
  1. Re-running the `docs/research/mxcli-inventory.md` process against the
     new tag (per ADR-0012).
  2. Updating `policy/mxcli-commands.json` with newly verified rows.
  3. Bumping `MIN_MXCLI` in `bin/doctor.py` and `_schema.mxcli_version` in
     `policy/mxcli-commands.json`.
  4. Reviewing any new override flags and extending ADR-0011 if needed.
- The pin moves on a merged PR with the above artefacts updated together.

## Consequences

- Positive: Predictable behaviour. The guard and the binary agree.
- Positive: Upgrade is a conscious act, with its own review.
- Negative: We lag upstream by one release while the inventory catches up.
  Acceptable: the guard treats unknown-at-pin as WRITE, so safety is
  preserved during the lag.
- Follow-ups: Automate the pin-move checklist as a script in a later phase.

## Versions

- mxcli: pinned at v0.26.0.

## References

- ADR-0007, ADR-0012.
- `docs/research/mxcli-inventory.md`.
