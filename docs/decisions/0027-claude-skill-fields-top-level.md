# ADR-0027: Generated Claude skills carry Claude-only fields at top level

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

Phase 2 put the `adapter.claude.json` sidecar into `metadata.claude` as a
JSON string to keep generated skills inside the Agent Skills spec. Claude
Code does not read fields there: its skills reference says `metadata` is
free-form data that "Claude Code doesn't act on". So
`disable-model-invocation: true` had no effect.

## Decision

- `core/skills/*/SKILL.md` stays spec-only (unchanged).
- The Claude adapter emits sidecar fields as top-level frontmatter keys in
  `plugins/mendix-agentic/skills/*/SKILL.md`: `disable-model-invocation`,
  `user-invocable`, `allowed-tools`, `context`, `agent`, `paths`, in that
  order. The `metadata.claude` encoding is removed.
- List values are YAML block lists, because items such as `Bash(git add:*)`
  or `**/*.{ts,tsx}` contain spaces and commas.
- The validator and the adapter reject unknown sidecar keys, and keys set
  both in `SKILL.md` and in the sidecar.

## Consequences

- Positive: Claude-only fields take effect.
- Positive: A misspelt field fails validation instead of being ignored.
- Negative: Generated Claude skills are no longer strictly spec-only; other
  agents' adapters must not copy them, and they should build from `core/`.

## Versions

- Claude Code: ≥ 2.1.281 (validated with `claude plugin validate` on 2.1.281
  and 2.1.305)
- Others: any

## References

- code.claude.com/docs/en/skills (frontmatter reference).
- ADR-0001, ADR-0021, ADR-0023.
