# ADR-0008: Mendix depth lives in skills and lint rules, not agent bios

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

Stuffing Mendix know-how into a role prompt ("you are a Mendix expert, always
remember to…") burns context, loses on compaction, and cannot be unit-tested.
It also duplicates mxcli's own bundled skills.

## Decision

Agent definitions (phase 3+) stay thin — role, scope, tools, hand-off rules.
Mendix depth lives in:

1. **Skills** (prose + examples), loaded only when relevant.
2. **Lint rules** (deterministic checks run by `mxcli lint`).
3. **References** to mxcli's own bundled skills — we point at them rather than
   copying their content.

## Consequences

- Positive: Role prompts stay small and legible; expertise is reusable
  across agents.
- Positive: We do not drift from mxcli's own guidance; we link to it.
- Negative: A new contributor has to look in several places to understand the
  "whole" of a role.
- Follow-ups: Phase 2 catalogues which mxcli skills we reference and which we
  wrap with extra context.

## Versions

- mxcli: ≥ v0.26.0 for bundled skills (target).
- All other components: any.

## References

- `AGENTS.md` non-negotiable 5.
- ADR-0001, ADR-0005.
