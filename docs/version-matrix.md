# Version matrix

Last reviewed: 2026-10-21. UNVERIFIED entries have not been reconfirmed since
the row was added — rerun the checks before relying on them.

| Component    | Minimum | Tested (target) | Notes                                                                                                       | Verified |
| ------------ | ------- | --------------- | ----------------------------------------------------------------------------------------------------------- | -------- |
| Claude Code  | 2.1.281 | 2.1.305         | Minimum set by the features below (ADR-0025); `bin/doctor` FAILs below it. Generated plugin validated with `claude plugin validate` on 2.1.281 and 2.1.305. Hook shell on Windows: Git Bash (see below). Not required to work on this repo; other agents are allowed. | Y |
| mxcli        | v0.26.0 | v0.26.0         | v0.26.0 released 2026-10-11 (github.com/mendixlabs/mxcli/releases). v0.27.0 is newer but out of phase 1 scope. | Y        |
| Studio Pro   | 11.12   | 11.12 LTS       | mxcli refuses writes while `<project>.mpr.lock` is present (cmd_exec.go, see mxcli-inventory.md).           | Y (lock-file check), UNVERIFIED (exact Studio Pro version floor) |
| Python       | 3.10    | 3.10, 3.11, 3.12 | Required for `bin/doctor.py` and `policy/mxcli_guard.py`. Stdlib only (ADR-0006).                           | Y        |
| git          | 2.30    | 2.40+           | Needed for pre-commit hooks and CRLF handling. No lower minimum enforced by `bin/doctor` today.             | UNVERIFIED |

**Note (2026-10-20):** mxcli v0.27.0 was released 2026-10-15 but we remain
pinned at v0.26.0 (ADR-0013). Any upgrade requires re-running
[`docs/research/mxcli-inventory.md`](research/mxcli-inventory.md) and
promoting the policy data (`policy/mxcli-commands.json`) before the pin
moves.

### Claude Code features that set the minimum (ADR-0025)

Each row cites the entry in
[CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
under the version heading shown. The minimum is the highest of them.

| Feature we rely on | Version | Changelog entry |
| ------------------ | ------- | --------------- |
| Native `AGENTS.md` reading | 2.1.277 | "Added AGENTS.md support: in a project with no CLAUDE.md, Claude Code reads AGENTS.md instead" |
| …on every provider (Bedrock, Vertex, Foundry, gateways, telemetry off) | **2.1.281** | "Changed AGENTS.md support to also work on Amazon Bedrock, Google Vertex AI, Microsoft Foundry, LLM gateways, and sessions with telemetry disabled" |
| `omitClaudeMd` in agent frontmatter, including plugin subagents | 2.1.271 | "Added `omitClaudeMd` to agent frontmatter and `--agents` JSON, letting custom and plugin subagents run without user, project and local CLAUDE.md files" |
| `Agent(...)` allowlist in a main-thread agent's `tools` | 2.1.33 | "Added support for restricting which sub-agents can be spawned via `Task(agent_type)` syntax in agent "tools" frontmatter" |
| …several types in one plugin agent's `tools` | 2.1.147 | "Fixed plugin agents that declare multiple `Agent(...)` types in `tools:` frontmatter dropping all but the last entry" |
| …enforced for named spawns | 2.1.186 | "Fixed `Agent(type)` deny rules and `Agent(x,y)` allowed-types restrictions not being enforced for named subagent spawns" |
| Plugin agent as main thread (`--agent`) | 2.0.59 / 2.1.143 | "Added --agent CLI flag…"; "Fixed `--agent <name>` not finding plugin-contributed agents without the `plugin:` prefix" |
| Plugin hooks | 2.0.12 / 2.1.69 | "Plugin System Released: … commands, agents, hooks, and MCP servers"; "Fixed plugin hooks being silently dropped when two plugins use the same `${CLAUDE_PLUGIN_ROOT}/...` command template" |
| Background subagents | 2.0.60 / 2.1.198 | "Added background agent support"; "Subagents now run in the background by default" |

Checked on 2026-10-21 against the changelog as of 2.1.306. Empirical checks
(hook shell, fail-closed hook, `--agent` launch, `Agent(...)` allowlist,
`displayName`) are in [`docs/install.md`](install.md).

### Claude Code hook shell

| Platform | Shell that runs plugin hook commands | Evidence |
| -------- | ------------------------------------ | -------- |
| Windows 11 | Git Bash: `$0=/usr/bin/bash`, `SHELL=/bin/bash.exe`, `BASH_VERSION=5.2.37(1)-release`; `%ComSpec%` not expanded | Diagnostic hook, Claude Code 2.1.305, Git for Windows 2.48.1 (docs/install.md) |
| Linux, macOS | `sh`/`bash` | UNVERIFIED by us; per code.claude.com/docs/en/hooks |

### Pinned mxcli binary (ADR-0032)

| Field       | Value                                                                   |
| ----------- | ----------------------------------------------------------------------- |
| Version     | v0.26.0                                                                 |
| Asset       | `mxcli-linux-amd64` (raw ELF binary, not an archive)                    |
| Size        | 102 301 856 bytes                                                       |
| SHA-256     | `c3fe5450931d52628777107c71617855db6acf606ef7df8815990ac3c55519ea`      |
| Source      | https://github.com/mendixlabs/mxcli/releases/download/v0.26.0/mxcli-linux-amd64 |

The same values live in [`policy/mxcli-pin.json`](../policy/mxcli-pin.json)
and are checked by the `mxcli-tree` CI job before the binary is executed.

## How to update this file

- When a component's floor shifts, add a row and keep the old one with a
  `Superseded by …` note in Notes.
- Pair every change with a `docs/mxcli-bugs.md` entry if it was driven by an
  upstream bug.
- An ADR is required for any change that moves the minimum of mxcli or
  Studio Pro.
