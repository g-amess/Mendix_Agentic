# ADR-0005: Guardrails are enforced by tool-agnostic policy scripts

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

Prose rules in markdown are ignored under pressure. The only rules an agent
cannot talk itself out of are rules the harness enforces. But we support
multiple harnesses, so the rules cannot live inside any single one.

## Decision

Guardrails are implemented as **tool-agnostic policy scripts** (phase 1:
`policy/mxcli_guard.py`). The same script is called:

1. From a Claude Code `PreToolUse` hook, consuming JSON on stdin and
   returning a JSON decision.
2. From a `git` pre-commit / pre-push hook on contributor machines.
3. From CI on every push and PR.
4. From any other agent harness that can shell out before running a tool.

Policy data (which commands write, who may write, which MDL statements are
banned) lives in **human-editable JSON** next to the script.

## Consequences

- Positive: One source of truth, enforced in every surface we care about.
- Positive: Non-Claude agents get the same guardrails as Claude.
- Negative: Hook authors must keep up with harness-specific payload shapes
  (e.g. Claude Code's `hookSpecificOutput.permissionDecision`).
- Follow-ups: Add adapters that install the hook into each tool's config.

## Versions

- mxcli: any
- Studio Pro: any
- Mendix runtime: any
- Python: 3.10+
- Claude Code: current PreToolUse schema at
  code.claude.com/docs/en/hooks (as of 2026-10-20).

## References

- `AGENTS.md` non-negotiable 5.
- ADR-0006, ADR-0007.
