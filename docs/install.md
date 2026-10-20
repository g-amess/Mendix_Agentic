# Installing the `mendix-agentic` Claude Code plugin

This repo is a Claude Code plugin marketplace (ADR-0022). The plugin lives at
`plugins/mendix-agentic/` and the marketplace manifest at
`.claude-plugin/marketplace.json`.

## Local-development install (what we tested on 2026-10-20)

```sh
# From the repo root. The `./` prefix is required — bare `.` returns
# "Invalid marketplace source format".
claude plugin marketplace add ./
# → ✔ Successfully added marketplace: mendix-agentic (declared in user settings)

claude plugin install mendix-agentic@mendix-agentic
# → ✔ Successfully installed plugin: mendix-agentic@mendix-agentic (scope: user)

claude plugin list
# → mendix-agentic@mendix-agentic   Version: 0.2.0-alpha   Status: ✔ enabled
```

The plugin is cached on Windows under
`~/.claude/plugins/cache/mendix-agentic/mendix-agentic/<version>/`.

### Verify the guard hook fires

The PreToolUse hook calls `python "${CLAUDE_PLUGIN_ROOT}/policy/mxcli_guard.py"`.
A quick end-to-end check (no real Mendix project needed):

```sh
PLUGIN_ROOT=~/.claude/plugins/cache/mendix-agentic/mendix-agentic/0.2.0-alpha

# Should DENY
echo '{"tool_name":"Bash","tool_input":{"command":"mxcli -p app.mpr exec m.mdl"}}' \
  | python "$PLUGIN_ROOT/policy/mxcli_guard.py"
# → "permissionDecision": "deny" with "Rule 5: `mxcli exec` is a WRITE …"

# Should ALLOW
echo '{"tool_name":"Bash","tool_input":{"command":"mxcli show modules"}}' \
  | python "$PLUGIN_ROOT/policy/mxcli_guard.py"
# → "permissionDecision": "allow"

# Should DENY (PowerShell is handled identically)
echo '{"tool_name":"PowerShell","tool_input":{"command":"mxcli -p app.mpr exec m.mdl"}}' \
  | python "$PLUGIN_ROOT/policy/mxcli_guard.py"
# → "permissionDecision": "deny"
```

### Uninstall

```sh
claude plugin uninstall mendix-agentic@mendix-agentic
claude plugin marketplace remove mendix-agentic
```

## Prerequisites

- Python 3.10+ on PATH as `python` (the hook invokes `python` so it works on
  both Windows and Linux). `bin/doctor` reports FAIL if an older Python or no
  `python` is on PATH.
- `claude` CLI (Claude Code) ≥ 2.1.128 is what we tested with.

## Known quirks (claude plugin validate)

- `displayName` in `plugin.json` is documented at
  code.claude.com/docs/en/plugins/manifest-reference but
  **rejected** by `claude plugin validate` on CLI 2.1.128. We omit it until
  the installed CLI accepts it (tracked for phase 3+).
- `claude plugin marketplace add` requires a path starting with `./` for
  a local directory; bare `.` returns "Invalid marketplace source format".
