# ADR-0033: CI check steps run independently

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

By default a GitHub Actions step is skipped once an earlier step in the
same job fails. For contributor PRs this means a single logging failure
in the `Doctor (JSON)` step hides the test suite's output, and we end up
pushing a fix that then surfaces another unrelated failure.

The check surface in this repo is small and self-contained: doctor,
`validate.py`, `build.py --check`, and the unittest suite each check a
different invariant. Running them independently gives one CI run that
reports every failure.

## Decision

- Each check step after checkout + Python setup carries `if: always()` so
  it runs even if an earlier step failed:
  - `Doctor (JSON)`
  - `Validate core/`
  - `Build --check (adapter drift)`
  - `Unit tests`
- The job itself still fails if any of the four reports non-zero, because
  GitHub Actions considers a job failed when any step with
  `if: always()` fails.
- The `mxcli-tree` job stays separate and keeps the default
  "stop on first failure" behaviour, because its single step is the
  entire job.

## Consequences

- Positive: One CI run reports every independent failure; contributor
  loops are shorter.
- Positive: A green run means every invariant was checked, not just the
  first few.
- Negative: If the checkout or Python-setup step fails, nothing else
  runs — that is correct, as the environment is prerequisites.
- Follow-ups: If we add a check that depends on an earlier step's
  artefact (e.g. a lint that needs the build output), gate it on that
  step's success instead of `always()`.

## Versions

Applies regardless of version.

## References

- `.github/workflows/ci.yml`.
- GitHub Actions docs on `if: always()`.
