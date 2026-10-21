# ADR-0028: Subagent tool lists are comma-separated strings, never YAML flow lists

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

Phase 2 emitted `tools: [Read, Grep, "Agent(analyst,writer)"]`. A YAML flow
list splits on commas, so an unquoted `Agent(a, b)` becomes two broken
items. The subagent docs give `tools` as a comma-separated string, for
example `tools: Agent(worker, researcher), Read, Bash`.

Testing a generated hub as the main thread (`claude --agent`) on Claude Code
2.1.305 and 2.1.281 showed a second problem. Plugin agents register under
`<plugin>:<name>`, and `Agent(spoke-a, spoke-b)` matched nothing: the Agent
tool reported "Available agents: none" and refused even the listed spokes.
`Agent(mendix-agentic:spoke-a, mendix-agentic:spoke-b)` let the spokes run
and still refused `general-purpose`.

## Decision

The adapter emits `tools:` as one comma-separated plain scalar, in
capability-map order, with the `Agent(...)` entry last. Spokes inside it are
namespaced with the plugin name and sorted:

    tools: Read, Grep, Glob, Agent(mendix-agentic:spoke-a, mendix-agentic:spoke-b)

## Consequences

- Positive: The hub's allowlist parses as one entry and actually admits its
  spokes.
- Negative: A rename of the plugin changes every hub's `tools` line;
  `PLUGIN_NAME` in `adapters/claude/build.py` is the single source.
- Follow-ups: Phase 3 starts the orchestrator with
  `claude --agent mendix-agentic:orchestrator` (docs/install.md).

## Versions

- Claude Code: ≥ 2.1.281 (tested on 2.1.281 and 2.1.305)
- Others: any

## References

- code.claude.com/docs/en/sub-agents ("Restrict which subagents can be
  spawned", `--agent` with plugin agents).
- `tests/adapt/test_build.py::TestHubToolsGolden`.
