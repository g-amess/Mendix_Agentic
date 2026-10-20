# ADR-0001: Canonical instructions live in plain markdown under `core/`

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

Agents come and go. Claude Code is first; Cursor, Aider, Copilot and whatever
replaces them must all be able to drive the same workflow. If we author
instructions inside a tool-specific layout (e.g. `.claude/agents/…`), we lock
ourselves to one vendor and have to port by hand each time a new tool arrives.

## Decision

All canonical content — role definitions, skills, workflows, prompts, lint
rules — lives as **plain markdown under `core/`**. Any file that only makes
sense to a specific tool (`.claude/`, `.cursor/`, project-level `AGENTS.md`
blocks, slash-command manifests, plugin bundles) is **generated** by an
adapter under `adapters/` and never hand-maintained.

## Consequences

- Positive: Adding a new agent is a new adapter, not a rewrite.
- Positive: Diff review focuses on `core/`; tool-specific files are derived.
- Negative: Adapters must be run (or checked into generated form) before a
  target repo can consume Mendix_Agentic.
- Follow-ups: Phase 2+ builds the first adapter (Claude Code).

## Versions

Applies regardless of version.

- mxcli: any
- Studio Pro: any
- Mendix runtime: any
- Python: 3.10+
- Claude Code: any

## References

- `AGENTS.md` non-negotiable 1.
