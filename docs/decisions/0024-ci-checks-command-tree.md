# ADR-0024: CI checks the installed mxcli's command tree against the inventory

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

`policy/mxcli-commands.json` is a snapshot of mxcli at the pinned SHA
(ADR-0013). If an mxcli release adds a subcommand, our inventory and the
guard's unlisted-child rule (ADR-0014) must evolve together. Catching
that drift by hand is brittle.

## Decision

- CI runs a `mxcli-tree` job on ubuntu that:
  1. Downloads the pinned mxcli linux release asset via the GitHub API.
  2. Runs `mxcli --help` recursively over the command tree
     (`--help` only — no project commands).
  3. Builds a sorted list of command paths and compares it to the keys
     in `policy/mxcli-commands.json`.
  4. Fails the job if commands are missing or extra, with the specific
     list.
- If the asset cannot be fetched (release not found, GitHub outage), the
  job fails loudly rather than skipping silently.
- The job runs on every push and pull request, not on cron: we want the
  check to gate merges, not to fire on a schedule.

## Consequences

- Positive: Drift between the installed mxcli and our policy data is a
  CI failure, not a surprise in production.
- Positive: Upgrading the pin (ADR-0013) is forced through the same
  check.
- Negative: CI depends on a GitHub-hosted release asset. If the pinned
  release is deleted or renamed, the job fails until the pin is updated.
- Follow-ups: Phase 3+ could add a `--learn` mode to the inventory
  checker that produces draft rows for new commands.

## Versions

- mxcli: pinned per ADR-0013.
- Guard: v1.2+.

## References

- ADR-0007, ADR-0013, ADR-0014.
- `.github/workflows/ci.yml` — `mxcli-tree` job.
