# ADR-0034: main came from phase-1-foundation; failing merges are fixed forward

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

`main` was created from `phase-1-foundation`, which by then already
contained Phases 1 and 2. The phase merges (PR #1, merge commit `78eaf9f`)
landed while the `mxcli command-tree check` job was failing. Rewriting
`main`'s history to undo that would break every clone and open branch.

## Decision

- `main`'s history stays as it is.
- Anything that merged with failing checks is fixed forward on a new branch
  from `main` (here `phase-2-finish`).
- A GitHub ruleset on `main` blocks merging unless the required checks pass.
  **Not yet in place:** on 2026-10-21 `gh api repos/g-amess/Mendix_Agentic/rulesets`
  returned `[]` and `…/branches/main/protection` returned "Branch not
  protected". A maintainer with admin rights must create it.

## Consequences

- Positive: History is honest and stable; once configured, the ruleset
  prevents a repeat.
- Negative: `main` carried a red check for a while.
- Follow-ups: Create the ruleset, requiring every job in
  `.github/workflows/ci.yml`, including `mxcli command-tree check`. Keep the
  required checks in step with the job names.

## Versions

Applies regardless of version.

## References

- ADR-0009, ADR-0029, ADR-0033.
