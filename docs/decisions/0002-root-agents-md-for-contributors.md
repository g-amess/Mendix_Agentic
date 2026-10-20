# ADR-0002: Root `AGENTS.md` is for contributors to this repo

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

`AGENTS.md` is becoming a de-facto standard — many agents read it on project
load. If we put shipped project content there, we conflate two audiences
(contributor to Mendix_Agentic vs. contributor to a downstream Mendix app) and
cannot evolve them separately.

## Decision

The root `AGENTS.md` describes **how to work on _this_ repo**: skeleton,
non-negotiables, how to record a decision. Shipped project content lives under
`core/` and is written into a downstream project's own `AGENTS.md` by an
adapter during `mxcli init` (or equivalent).

## Consequences

- Positive: Clear separation of audiences.
- Positive: We can version shipped content independently of contributor rules.
- Negative: One extra indirection for new contributors ("why isn't the agent
  reading the root AGENTS.md on the target project?").
- Follow-ups: Document the adapter-generated AGENTS.md block in phase 2.

## Versions

Applies regardless of version.

- mxcli: any
- Studio Pro: any
- Mendix runtime: any
- Python: any
- Claude Code: any

## References

- ADR-0001.
