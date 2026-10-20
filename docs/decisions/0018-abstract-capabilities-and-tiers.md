# ADR-0018: Role cards declare abstract capabilities and model tiers

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

If a role card names Claude Code tools (`Bash`, `Grep`, `Agent(…)`) and model
aliases (`sonnet`, `opus`) directly, it is tied to one harness forever.
Replacing Claude with Cursor or Aider becomes a rename job across every
role.

## Decision

A role card declares:

- `capabilities`: entries from `core/capabilities.json` such as
  `read-files`, `mxcli-read`, `mxcli-write`, `delegate`, `ask-human`.
- `model_tier`: `fast`, `standard`, or `deep`.

Adapters map these to tool-specific tool names and model aliases via
`adapters/<tool>/capability-map.json`. The Claude adapter maps `mxcli-read`
to `Bash`, `model_tier: deep` to `opus`, etc. A hypothetical Cursor
adapter could map the same capability to its own tool name.

## Consequences

- Positive: One role card feeds every adapter.
- Positive: Capability drift between adapters is a bug in the capability
  map, not in the role card.
- Negative: A new capability requires both a registry entry and a map
  entry in every active adapter.
- Follow-ups: Phase 3+ adds a `cursor` adapter and extends the capability
  map accordingly.

## Versions

Applies regardless of version.

## References

- `core/capabilities.json`, `adapters/claude/capability-map.json`.
- ADR-0001, ADR-0022, ADR-0023.
