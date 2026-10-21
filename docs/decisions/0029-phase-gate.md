# ADR-0029: No phase starts until the previous phase is merged with green CI

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

Phases 1 and 2 overlapped: Phase 2 branched before Phase 1's fixes landed,
and both reached `main` together with a failing check (see ADR-0034). Work
built on an unmerged phase inherits its open problems and makes review
harder.

## Decision

A phase branch is created from `main` only after the previous phase's PR is
merged and CI on `main` is green. Fixes found later go forward on a new
branch from `main`.

## Consequences

- Positive: Each phase reviews against a known-good base.
- Negative: Phases cannot be pipelined; a slow review blocks the next phase.

## Versions

Applies regardless of version.

## References

- ADR-0009 (branch per phase, PR only), ADR-0034.
