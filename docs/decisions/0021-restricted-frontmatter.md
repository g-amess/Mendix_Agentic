# ADR-0021: Canonical frontmatter is a restricted YAML subset

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

YAML is forgiving. "Full" YAML allows anchors, tags, nested mappings,
multi-line strings, dates, nulls, and floats — most of which we would
have to reject anyway because they do not round-trip through our
adapters. Using a full YAML parser means pulling in a third-party library
(PyYAML / ruamel), which breaks ADR-0006 (stdlib only), or writing a
hand-rolled parser that has to decide what to do with every YAML corner
case.

## Decision

- Canonical frontmatter is a **restricted YAML subset**, parsed by
  `adapters/lib/frontmatter.py` (stdlib only).
- Supported: string scalars (plain, single- or double-quoted; double
  quotes accept `\"` and `\\`); booleans; integers; block lists; flow
  lists; **one** level of nested mapping with scalar values (needed for
  the Agent Skills `metadata` field).
- Everything else is rejected with a file:line error. No multi-line
  strings. No `null`. No floats. No nested lists. No deeper mappings. No
  anchors or tags.
- Tool-specific extras (Claude Code: `disable-model-invocation`,
  `user-invocable`, `allowed-tools` lists, etc.) live in JSON sidecars
  next to the role card or skill (`adapter.claude.json`), not in the
  canonical frontmatter.

## Consequences

- Positive: No third-party parser dependency.
- Positive: Every valid file round-trips through the emitter.
- Negative: An author who writes a legitimate YAML pattern we reject has
  to rewrite it. We mitigate with clear error messages.
- Follow-ups: If a specific YAML feature becomes necessary, extend the
  parser deliberately — do not switch to full YAML.

## Versions

- Python: 3.10+ (per ADR-0006).

## References

- `adapters/lib/frontmatter.py`.
- ADR-0006.
- Agent Skills spec, agentskills.io/specification.
