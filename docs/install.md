# Installing the `mendix-agentic` Claude Code plugin

This repo is a Claude Code plugin marketplace (ADR-0022). The plugin lives at
`plugins/mendix-agentic/` and the marketplace manifest at
`.claude-plugin/marketplace.json`.

Claude Code versions: minimum **2.1.281**, tested on **2.1.305**
(ADR-0025, `docs/version-matrix.md`). Every result on this page was observed
on Windows 11 with Claude Code 2.1.305 on 2026-10-21 unless a line says
otherwise.

## Prerequisites

- Claude Code ≥ 2.1.281. `bin/doctor` FAILs below that; the fix is
  `claude update`, and in VS Code also update the extension and restart.
- Python ≥ 3.10 reachable as **`python`**. The hook runs `python`, not
  `py -3`: hooks run under bash on every platform, and `py` exists only on
  Windows (ADR-0026). `bin/doctor` checks that `python` resolves to ≥ 3.10.
  On Windows, use the python.org installer with "Add python.exe to PATH",
  and turn off the `python.exe`/`python3.exe` App execution aliases if they
  shadow it.
- Windows: Git for Windows (Claude Code runs hooks under its bash; see below).

## Local-development install

```sh
# From the repo root. The `./` prefix is required — bare `.` returns
# "Invalid marketplace source format".
claude plugin marketplace add ./
claude plugin install mendix-agentic@mendix-agentic
claude plugin list
# → mendix-agentic@mendix-agentic   Version: <VERSION>   Status: ✔ enabled
```

The plugin is cached under
`~/.claude/plugins/cache/mendix-agentic/mendix-agentic/<version>/`.

For a one-session load without installing, pass the directory instead:
`claude --plugin-dir plugins/mendix-agentic`. It then shows as
`mendix-agentic@inline`.

### Verify the guard decides correctly

```sh
PLUGIN_ROOT=~/.claude/plugins/cache/mendix-agentic/mendix-agentic/<version>

# Should DENY
echo '{"tool_name":"Bash","tool_input":{"command":"mxcli -p app.mpr exec m.mdl"}}' \
  | python "$PLUGIN_ROOT/policy/mxcli_guard.py"
# → "permissionDecision": "deny" with "Rule 5: `mxcli exec` is a WRITE …"

# Should ALLOW
echo '{"tool_name":"Bash","tool_input":{"command":"mxcli show modules"}}' \
  | python "$PLUGIN_ROOT/policy/mxcli_guard.py"
# → "permissionDecision": "allow"
```

### Uninstall

```sh
claude plugin uninstall mendix-agentic@mendix-agentic
claude plugin marketplace remove mendix-agentic
```

## Which shell runs plugin hook commands on Windows

**Git Bash.** A scratch plugin outside this repo had one PreToolUse hook on
`Bash`:

```sh
echo "dollar0=$0 SHELL=$SHELL COMSPEC=%ComSpec% BASH_VERSION=$BASH_VERSION" >> <scratch>/probe.log
```

After `claude -p "Use the Bash tool to run exactly: echo probe-ok" --plugin-dir <scratch> --allowedTools Bash`
the log held:

```
dollar0=/usr/bin/bash SHELL=/bin/bash.exe COMSPEC=%ComSpec% BASH_VERSION=5.2.37(1)-release
```

`$…` expanded and `%ComSpec%` did not, so cmd.exe was not involved. Git for
Windows 2.48.1. The same probe is the re-test on a new Claude Code version.

## Fail-closed hook: evidence (ADR-0026)

The generated hook command is:

```sh
python "${CLAUDE_PLUGIN_ROOT}/policy/mxcli_guard.py" || { echo 'mendix-agentic guard could not run — run bin/doctor' >&2; exit 2; }
```

Method: a scratch plugin outside the repo, with one PreToolUse hook on `Bash`
whose command was varied per run. Each run was

```sh
claude -p "Use the Bash tool exactly once to run: echo ran > marker.txt . Do not retry if it is blocked. Then report verbatim any error text you saw." \
  --plugin-dir <scratch> --allowedTools Bash
```

from an empty working directory. Whether `marker.txt` exists afterwards is
the result; the model's report only supplies the error text.

| Run | Hook command | `marker.txt` | Result |
| --- | ------------ | ------------ | ------ |
| Control | `python-does-not-exist ".../mxcli_guard.py"` (no wrapper) | created | **Not blocked** — exit 127 is a non-blocking error. This is the gap ADR-0026 closes. |
| (a) missing interpreter | `python-does-not-exist ".../mxcli_guard.py" \|\| { …; exit 2; }` | absent | **Blocked** |
| (b) guard raises | `python ".../boom.py" \|\| { …; exit 2; }`, where `boom.py` is `raise RuntimeError("deliberate guard failure")` | absent | **Blocked** |
| (c) real guard, harmless command | `python ".../mxcli_guard.py" \|\| { …; exit 2; }` with the real policy files | created | Allowed — the wrapper does not get in the way |

Error text Claude Code showed for (a):

```
PreToolUse:Bash hook error: [...]: /usr/bin/bash: line 1: python-does-not-exist: command not found
mendix-agentic guard could not run — run bin/doctor
```

and for (b):

```
PreToolUse:Bash hook error: [...]: Traceback (most recent call last):
  File "...\policy\boom.py", line 1, in <module>
    raise RuntimeError("deliberate guard failure")
RuntimeError: deliberate guard failure
mendix-agentic guard could not run — run bin/doctor
```

The scratch plugin was deleted afterwards.

## Running a plugin agent as the main thread

Phase 3 starts the orchestrator this way:

```sh
claude --agent mendix-agentic:orchestrator
```

Checked with a generated fixture hub (`tests/fixtures/core/hub_two_spokes`)
loaded via `--plugin-dir`:

- `claude --agent mendix-agentic:hub` and the bare `claude --agent hub` both
  start the hub; the session's tools are exactly `Read, Grep, Glob, Agent`.
  Use the namespaced form; the bare name is ambiguous once two plugins ship
  an agent with the same name.
- **The `Agent(...)` allowlist must use namespaced names.** With
  `tools: Read, Grep, Glob, Agent(spoke-a, spoke-b)` every spawn failed,
  including the listed spokes: `Agent type 'spoke-a' not found. Available agents: none`.
  With `Agent(mendix-agentic:spoke-a, mendix-agentic:spoke-b)`,
  `mendix-agentic:spoke-b` ran and replied, while `general-purpose` was refused:
  `Agent type 'general-purpose' not found. Available agents: mendix-agentic:spoke-a, mendix-agentic:spoke-b`.
  The bare `spoke-a` was refused the same way. Same result on Claude Code
  2.1.281. The adapter therefore emits namespaced spokes (ADR-0028).

## `claude plugin validate`

- The built plugin, the `valid` fixture and the `hub_two_spokes` fixture all
  report "✔ Validation passed" on Claude Code 2.1.281 and 2.1.305.
- `displayName` in `plugin.json` was rejected on 2.1.128. It is accepted on
  2.1.281 and 2.1.305, so the adapter emits it again.
- The validator's plugin-directory checks (README length, icon) are only
  listing requirements for the public directory; they do not affect the
  result.
- `claude plugin marketplace add` requires a path starting with `./` for a
  local directory; bare `.` returns "Invalid marketplace source format"
  (observed on 2.1.128; not re-tested).
