# ADR-0009: Work happens on a branch per phase, merged via PR

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The repo's history is the audit trail for guardrails and policy data. Direct
pushes to `main` make it hard to answer "when did this rule arrive and why?",
and expose the branch to half-finished work. Agents in particular should not
be able to land changes without a human in the loop.

## Decision

- `main` is protected: direct push disabled, PRs require passing CI, and
  linear history is preferred.
- Work for each phase lives on a branch named `phase-N-<slug>` (e.g.
  `phase-1-foundation`). ADRs, docs, policy data and code change together on
  that branch.
- Agents **never commit to `main`**. The last human-review step is the PR
  merge, and merging is a human action.

## Consequences

- Positive: Every change to canonical content has a reviewed PR behind it,
  which is the audit trail we need for the policy data in particular.
- Positive: CI gates (doctor + unittests) run on every push.
- Negative: Minor friction for one-line docs tweaks; acceptable.
- Follow-ups: Enable branch protection and required status checks on the
  GitHub repo (one-time admin task, not committed here).

## Versions

Applies regardless of version.

## References

- ADR-0010, ADR-0012.
