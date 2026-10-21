# ADR-0037: CI runs on pull requests and on pushes to main only

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

The workflow ran on every `push` and every `pull_request`. A branch with an
open PR therefore ran every job twice per push, including the mxcli tree
walk, which downloads a ~100 MB binary.

## Decision

`.github/workflows/ci.yml` triggers on `pull_request`, and on `push` only to
`main`. There is no `workflow_dispatch` today; if one is added later, keep
it.

## Consequences

- Positive: One run per PR update; `main` is still checked after each merge.
- Negative: A branch pushed without a PR gets no CI. Open a draft PR to get
  checks early.

## Versions

Applies regardless of version.

## References

- ADR-0024, ADR-0033, ADR-0034.
