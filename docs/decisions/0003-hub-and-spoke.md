# ADR-0003: Hub and spoke; the orchestrator is the main thread

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

Agent-to-agent calls fan out quickly, waste context and make audit trails
hard to reconstruct. Mendix model edits in particular need a single, serial
authority to avoid two agents pushing conflicting MDL at the same `.mpr`.

## Decision

The **orchestrator runs as the main thread** (`claude --agent <orchestrator>`
or the equivalent for other tools). Spokes (analyst, writer, reviewer, …) run
as subagents and **never call each other**. Every hand-off between spokes
goes via the orchestrator and must leave a **written artefact** in the repo
(a note, a draft script, a check result).

## Consequences

- Positive: Single serial authority over `.mpr` writes.
- Positive: Audit trail falls out of the artefacts themselves.
- Negative: Orchestrator context fills faster; mitigate with written artefacts
  so it does not need to carry every intermediate.
- Follow-ups: Phase 3 defines the orchestrator role and the artefact schema.

## Versions

Applies regardless of version.

- mxcli: any
- Studio Pro: any
- Mendix runtime: any
- Python: any
- Claude Code: any

## References

- `AGENTS.md` non-negotiable 2.
