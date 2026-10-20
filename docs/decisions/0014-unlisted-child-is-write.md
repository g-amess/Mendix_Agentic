# ADR-0014: Unlisted mxcli command paths are WRITE; children never inherit READ

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

mxcli's cobra tree is nested: `auth`, `brain`, `catalog`, `docker`,
`marketplace`, `skill`, `theme`, etc. are READ or WRITE *parents*, with
individual subcommands of either class. The first draft of the guard
treated `mxcli skill sync` the same as `mxcli skill` — if the parent was
READ, the whole thing was allowed, even though `skill sync` is not a
registered subcommand (it is a typo for `skill upgrade`).

That is the exact shape of an agent reaching for a plausible-but-wrong
command. If the fallback is "allow, because the parent is read-only", a
single typo escapes the guard.

## Decision

- `policy/mxcli-commands.json` keys are *paths*, up to depth 3
  (`auth hub login`, `theme switcher install`).
- `_lookup_subcommand` tries depth 3, then 2, then 1 — but **only** falls
  back to the parent entry if the parent is a *leaf* (no other key starts
  with `<parent> `).
- If the parent is a known *parent* (any other key starts with
  `<parent> `) and the invocation has 2+ positional tokens, an unlisted
  child returns None → **WRITE**, regardless of the parent's class.
- Falling back to a WRITE parent is fine (still WRITE). Falling back to a
  READ parent is forbidden.

## Consequences

- Positive: Unknown subcommands fail safely without manually tracking every
  valid variant.
- Positive: A new upstream subcommand after an upgrade is denied until the
  inventory is updated and a reviewed PR adds the entry.
- Negative: A legitimate new child needs a commands.json entry before it
  can be used, which is friction for exploratory work.
- Follow-ups: Phase 2+ could add a `--learn` mode that produces draft
  entries from captured `--help` output.

## Versions

- mxcli: pinned at v0.26.0 (per ADR-0013).
- Guard: policy/mxcli_guard.py v1.2+.

## References

- ADR-0007, ADR-0012, ADR-0013.
- `policy/mxcli_guard.py` — `_lookup_subcommand`, rule R4.
