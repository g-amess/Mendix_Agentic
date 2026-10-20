# ADR-0019: `policy/ownership.json` is generated from role cards

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

`policy/ownership.json` is the guard's rule-R5 input: it says which agent
is permitted which write classes. Hand-maintaining it alongside the role
cards invites drift — someone adds a `writer` role but forgets to add its
`owns` entry to the policy, so the guard denies the role's legitimate
work.

## Decision

- `policy/ownership.json` is **generated** by `adapters/claude/build.py`
  from the `owns` field of every role card with `access: write`.
- The file carries a `_comment` field with `GENERATED FROM core/ BY
  adapters/claude/build.py — DO NOT EDIT`.
- CI runs `python adapters/claude/build.py --check`, which fails on any
  drift between the committed `policy/ownership.json` and the file the
  generator would produce.

## Consequences

- Positive: One source of truth for ownership — the role cards.
- Positive: The guard tests continue to pass because the generated file
  has the same schema the hand-written seed had.
- Negative: An out-of-band change to `policy/ownership.json` is reverted
  on the next build. If a reviewer wants to grant a role an exception,
  they must change the role card instead.
- Follow-ups: If a tool-specific adapter needs a different ownership
  mapping, add a tool-specific override file next to the role card
  (phase 3+).

## Versions

Applies regardless of version.

## References

- ADR-0004 (one writer per class).
- ADR-0005, ADR-0020.
- `adapters/claude/build.py` — `_generate_ownership`.
