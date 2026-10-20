# ADR-0012: mxcli command classifications come from source or `--help`

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The first draft of `docs/research/mxcli-inventory.md` was built from
GitHub web summaries. It drifted away from the code in subtle ways
(descriptions paraphrased, aliases missed, side-effects glossed over) and
promoted `verified: true` on rows the author had not actually read.

## Decision

A command may be marked `verified: true` in `policy/mxcli-commands.json`
only on evidence of one of the following:

1. A code read at the **pinned tag** (`v0.26.0`), with a permalink to
   `mendixlabs/mxcli` at a specific commit SHA, OR
2. A captured `mxcli <cmd> --help` under
   `docs/research/mxcli-help/v0.26.0/<cmd>.txt`, taken from a locally
   installed mxcli at the pinned version.

Classifications derived from web summaries, blog posts, release notes, or
agent memory are **not** acceptable evidence. The sub-agent that wrote a
row writes the evidence trail at the same time.

## Consequences

- Positive: The policy data is only as current as the code it was last
  verified against — but we can tell exactly when that was.
- Positive: Upgrading the pin forces a re-verification pass.
- Negative: Verification is slow (every row needs a code read).
  Acceptable: the guard treats unverified rows as WRITE anyway (ADR-0007),
  so progress is incremental and safe.
- Follow-ups: Add an `inventory-check` script in a later phase that cross-
  references installed mxcli's `--help` output against the pinned
  classifications.

## Versions

- mxcli: whichever version is pinned by ADR-0013.

## References

- ADR-0007, ADR-0013.
