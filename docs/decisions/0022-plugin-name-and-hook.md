# ADR-0022: The Claude Code plugin is `mendix-agentic`; this repo is its marketplace

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

A plugin needs a name, a hook mechanism for the guard, and a place for
users to install it from. Claude Code supports a `.claude-plugin/
marketplace.json` at a git repo root (see code.claude.com/docs/en/plugins/
create-marketplace).

## Decision

- The plugin is named `mendix-agentic` and lives under
  `plugins/mendix-agentic/`. Its manifest is at
  `plugins/mendix-agentic/.claude-plugin/plugin.json`.
- The repo root carries `.claude-plugin/marketplace.json`, listing one
  plugin entry (`mendix-agentic`) with a relative-path `source`.
- The plugin ships the policy guard as a **PreToolUse** hook defined in
  `plugins/mendix-agentic/hooks/hooks.json`. The hook runs
  `python "${CLAUDE_PLUGIN_ROOT}/policy/mxcli_guard.py"` against the
  matchers `Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit`. The
  guard reads stdin as PreToolUse JSON and emits
  `hookSpecificOutput.permissionDecision`.
- `python` is the invocation; `bin/doctor` enforces Python ≥3.10. If a
  host does not have `python` on PATH (common on Windows without the
  official installer), the hook fails closed and the user runs
  `bin/doctor` for the actionable fix.

## Consequences

- Positive: One install command gets agents + guard together.
- Positive: Any Claude Code session reaching for `Bash`, `PowerShell`,
  `Edit`, or related tools goes through the guard first.
- Negative: Plugin subagents ignore `hooks`/`mcpServers`/`permissionMode`
  per the Claude Code docs — the hook sits at the plugin level, not on
  the subagent. The adapter deliberately does not emit those fields on
  subagents (ADR-0016).
- Follow-ups: Phase 6+ ships a project-level `.claude/settings.json`
  template with a stricter `permissions.deny` list that complements the
  hook.

## Versions

- Claude Code: current PreToolUse schema at code.claude.com/docs/en/hooks.
- Plugin schema: current manifest reference at
  code.claude.com/docs/en/plugins/manifest-reference.

## References

- ADR-0005, ADR-0010, ADR-0016, ADR-0020.
- `plugins/mendix-agentic/hooks/hooks.json`.
- `.claude-plugin/marketplace.json`.
