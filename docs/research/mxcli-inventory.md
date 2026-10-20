# mxcli inventory (v0.26.0)

Last reviewed: 2026-10-20. Source of record: `mendixlabs/mxcli` at tag
[`v0.26.0`](https://github.com/mendixlabs/mxcli/tree/v0.26.0). All rows
below were derived by reading the Go source in a local clone of that tag at
SHA `12ce281622a1a78ebb6737e61fe6b5ea78c59e45`. Anything still UNVERIFIED
(see section 7) is treated as **WRITE** by the policy guard (ADR-0007).

## 1. Version used

- Tag: [`v0.26.0`](https://github.com/mendixlabs/mxcli/tree/v0.26.0).
- Resolved SHA: `12ce281622a1a78ebb6737e61fe6b5ea78c59e45`.
- Permalink base: `https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/<path>#L<line>` (the `/v0.26.0/` tag form also resolves and is used below for readability).
- **Newer tag out of scope for this pin:** v0.27.0 (released 2026-10-15). ADR-0013 keeps the project pinned at v0.26.0; any upgrade requires re-running this inventory before relying on it.

## 2. Command tree

Cobra command registrations are rooted in `cmd/mxcli/main.go` (lines 437–462)
and in each file's own `init()` via `rootCmd.AddCommand(...)`. The tables
below group commands by their parent. "Verified" means a human read the
command's `Short`/`Long`, `RunE`/`Run`, and chased every write path reached
from it at this SHA.

### 2.1 Root commands

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| (root, no sub) | READ | Y | [cmd/mxcli/main.go#L106-L217](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/main.go#L106-L217) | Interactive REPL (also `-c` for one-liner). Reads project; no `.mpr` write except via explicit MDL statements. |
| `version` | READ | Y | [cmd/mxcli/cmd_version.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_version.go#L17) | Prints build info. |
| `changelog` | READ | Y | [cmd/mxcli/cmd_changelog.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_changelog.go#L17) | Prints embedded CHANGELOG. |
| `syntax` | READ | Y | [cmd/mxcli/help.go#L17-L96](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/help.go#L17-L96) | MDL syntax reference from the embedded registry. |
| `init` | WRITE | Y | [cmd/mxcli/init.go#L65-L686](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L65-L686) | Writes `.ai-context/`, `.claude/` or other tool directories, `CLAUDE.md`, `AGENTS.md`, lint-config, skills tree, lint-rules, companion mod, `mdlsource/`. Distinct from `add-tool` (see §4). |
| `add-tool` | WRITE | Y | [cmd/mxcli/cmd_add_tool.go#L16-L277](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_add_tool.go#L16-L277) | Writes tool-specific config files from `SupportedTools` map; does not run `init`'s universal setup. |
| `show` (alias `list`) | READ | Y | [cmd/mxcli/cmd_show.go#L13-L82](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_show.go#L13-L82) | Dispatches to MDL `SHOW …`. **Watch-out:** can trigger implicit catalog build (see §2.9). |
| `describe` | READ | Y | [cmd/mxcli/cmd_describe.go#L18-L225](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_describe.go#L18-L225) | Dispatches to MDL `DESCRIBE …`. **Watch-out:** reads `.mxcli/catalog.db`, may build it. |
| `search` | READ | Y | [cmd/mxcli/cmd_query.go#L225-L290](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L225-L290) | Full-text catalog search. **Watch-out:** builds `.mxcli/catalog.db` on first use. |
| `callers` | READ | Y | [cmd/mxcli/cmd_query.go#L15-L43](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L15-L43) | Runs MDL `SHOW CALLERS OF`. **Watch-out:** catalog cache write. |
| `callees` | READ | Y | [cmd/mxcli/cmd_query.go#L45-L73](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L45-L73) | Runs MDL `SHOW CALLEES OF`. **Watch-out:** catalog cache write. |
| `refs` | READ | Y | [cmd/mxcli/cmd_query.go#L75-L99](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L75-L99) | Runs MDL `SHOW REFERENCES TO`. **Watch-out:** catalog cache write. |
| `impact` | READ | Y | [cmd/mxcli/cmd_query.go#L101-L127](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L101-L127) | Runs MDL `SHOW IMPACT OF`. **Watch-out:** catalog cache write. |
| `structure` | READ | Y | [cmd/mxcli/cmd_query.go#L129-L172](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L129-L172) | Runs MDL `DESCRIBE STRUCTURE`. **Watch-out:** catalog cache write. |
| `context` | READ | Y | [cmd/mxcli/cmd_query.go#L174-L223](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L174-L223) | Runs MDL `DESCRIBE CONTEXT OF`. **Watch-out:** catalog cache write. |
| `check` | READ | Y | [cmd/mxcli/cmd_check.go#L21-L595](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check.go#L21-L595) | Validates MDL script(s). **Watch-out:** script-set form (>1 file) creates a scratch-copy project in `os.TempDir()` via `scriptdiff.NewScratch`, used and deleted on exit; may build `.mxcli/catalog.db`. The real `.mpr` is never touched. |
| `check --post-migration` | READ | Y | [cmd/mxcli/cmd_check.go#L482-L510](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check.go#L482-L510) | Legacy-widget scan. Read-only. |
| `diff` | READ | Y | [cmd/mxcli/cmd_diff.go#L19-L125](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_diff.go#L19-L125) | Runs the script on a scratch copy and diffs against the project. **Watch-out:** scratch-copy write to a temp dir (deleted). |
| `diff-local` | READ | Y | [cmd/mxcli/cmd_diff.go#L_(diffLocalCmd)](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_diff.go) | Git-ref diff (reads prior commits). |
| `lint` | READ | Y | [cmd/mxcli/cmd_lint.go#L19-L300](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_lint.go#L19-L300) | Runs built-in + Starlark rules. **Watch-out:** builds `.mxcli/catalog.db`. |
| `report` | WRITE | Y | [cmd/mxcli/cmd_report.go#L18-L80](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_report.go#L18-L80) | Runs `REFRESH CATALOG FULL` (writes `.mxcli/catalog.db`); with `--output` writes report file. Even without `-o`, cache write is unavoidable. Classified WRITE because of the mandatory full-mode cache build. |
| `graph-report` | WRITE | Y | [cmd/mxcli/cmd_graph_report.go#L21](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_graph_report.go#L21) | Same shape as `report`: catalog build + optional `--output` file. |
| `exec` | WRITE | Y | [cmd/mxcli/cmd_exec.go#L17-L161](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go#L17-L161) | Executes MDL against the `.mpr`. Lock-file check (§6); `--no-check` skips pre-flight; `--force` bypasses Studio Pro lock. |
| `fmt` | WRITE | Y | [cmd/mxcli/cmd_fmt.go#L26](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fmt.go#L26) | Formatter; `-w` writes files in place. |
| `rename` | WRITE | Y | [cmd/mxcli/cmd_rename.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_rename.go#L17) | Rewrites the `.mpr`. |
| `new` | WRITE | Y | [cmd/mxcli/cmd_new.go#L20](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_new.go#L20) | Creates a new project scaffold. |
| `run` | WRITE | Y | [cmd/mxcli/cmd_run.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run.go#L18) | Boots the app locally; writes deployment artefacts, logs, lifecycle state. |
| `serve` | WRITE | Y | [cmd/mxcli/serve.go#L37-L72](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/serve.go#L37-L72) | Starts HTTP visualization server on `--port`; builds catalog; binds a port. Not an MCP server (see §5). |
| `lsp` | WRITE | Y | [cmd/mxcli/lsp.go#L24](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/lsp.go#L24) | Starts a long-running Language Server over stdio. |
| `tui` | WRITE | Y | [cmd/mxcli/cmd_tui.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_tui.go#L15) | Interactive TUI; writes session state. |
| `project-tree` | READ | Y | [cmd/mxcli/project_tree.go#L41](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/project_tree.go#L41) | Prints tree. **Watch-out:** likely catalog cache write. |
| `test` | WRITE | Y | [cmd/mxcli/cmd_test_run.go#L15-L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_test_run.go#L15-L16) | Runs tests; boots runtime; writes deployment + logs. |
| `playwright` | WRITE | Y | [cmd/mxcli/cmd_playwright.go#L19](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L19) | Browser automation parent; subcommands write screenshots/traces. |
| `extract-templates` | WRITE | Y | [cmd/mxcli/cmd_extract_templates.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_extract_templates.go#L18) | Writes templates to disk. |
| `sync-java-deps` | WRITE | Y | [cmd/mxcli/cmd_sync_java_deps.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_sync_java_deps.go#L15) | Rewrites project Java deps. |
| `sql` | READ | Y | [cmd/mxcli/cmd_sql.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_sql.go#L16) | Runs SQL against external DB (per flags); read-only in intent, but a user-supplied query can mutate the external DB. Classify READ; the caller owns query content. |
| `oql` | READ | Y | [cmd/mxcli/docker_oql.go#L14](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker_oql.go#L14) | OQL query runner (SELECT-shaped). |
| `tunnel-hub` | WRITE | Y | [cmd/mxcli/cmd_tunnelhub.go#L25-L223](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_tunnelhub.go#L25-L223) | Long-running hub service; writes PID/state. Linux-only. |

### 2.2 `auth` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `auth` | WRITE | Y | [cmd/mxcli/cmd_auth.go#L28](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L28) | Credential subtree. |
| `auth login` | WRITE | Y | [cmd/mxcli/cmd_auth.go#L46](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L46) | Writes `~/.mxcli/auth.json`. |
| `auth logout` | WRITE | Y | [cmd/mxcli/cmd_auth.go#L62](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L62) | Rewrites credential store. |
| `auth status` | READ | Y | [cmd/mxcli/cmd_auth.go#L68](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L68) | |
| `auth list` | READ | Y | [cmd/mxcli/cmd_auth.go#L74](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L74) | |
| `auth hub login` | WRITE | Y | [cmd/mxcli/cmd_auth_hub.go#L39](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go#L39) | Writes credential store. |
| `auth hub status` | READ | Y | [cmd/mxcli/cmd_auth_hub.go#L45](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go#L45) | |
| `auth hub logout` | WRITE | Y | [cmd/mxcli/cmd_auth_hub.go#L51](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go#L51) | |

### 2.3 `brain` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `brain` | WRITE | Y | [cmd/mxcli/cmd_brain.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L25) | Research "brain" store. |
| `brain init` | WRITE | Y | [cmd/mxcli/cmd_brain.go#L65](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L65) | Creates store under `.claude/brain/`. |
| `brain capture <text>` | WRITE | Y | [cmd/mxcli/cmd_brain.go#L85](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L85) | Writes a shard. |
| `brain staged` | READ | Y | [cmd/mxcli/cmd_brain.go#L129](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L129) | Lists staged shards. |
| `brain promote <id>` | WRITE | Y | [cmd/mxcli/cmd_brain.go#L191](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L191) | |
| `brain drop <id>` | WRITE | Y | [cmd/mxcli/cmd_brain.go#L222](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L222) | |
| `brain show [shard]` | READ | Y | [cmd/mxcli/cmd_brain.go#L248](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L248) | |
| `brain resolve <id> <answer>` | WRITE | Y | [cmd/mxcli/cmd_brain.go#L288](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L288) | |
| `brain plan` | READ | Y | [cmd/mxcli/cmd_brain.go#L321](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L321) | |
| `brain brief` | READ | Y | [cmd/mxcli/cmd_brain.go#L391](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L391) | |
| `brain check` | READ | Y | [cmd/mxcli/cmd_brain.go#L455](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L455) | |

### 2.4 `bson` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `bson` | READ | Y | [cmd/mxcli/cmd_bson.go#L8](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson.go#L8) | |
| `bson dump` | READ | Y | [cmd/mxcli/cmd_bson_dump.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson_dump.go#L18) | Dumps a unit to stdout. |
| `bson discover` | READ | Y | [cmd/mxcli/cmd_bson_discover.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson_discover.go#L16) | |

### 2.5 `catalog` subtree

**Important:** this is the external Mendix Catalog service (`catalog.mendix.com`),
NOT the local MDL `CATALOG` keyword.

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `catalog` | READ | Y | [cmd/mxcli/cmd_catalog.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L16) | Requires `auth login`. |
| `catalog search <query>` | READ | Y | [cmd/mxcli/cmd_catalog.go#L33-L116](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L33-L116) | Remote HTTP read. |
| `catalog show <uuid>` | READ | Y | [cmd/mxcli/cmd_catalog.go#L46-L185](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L46-L185) | Remote HTTP read. |

### 2.6 `constant` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `constant` | WRITE | Y | [cmd/mxcli/cmd_constant.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L18) | |
| `constant set` | WRITE | Y | [cmd/mxcli/cmd_constant.go#L46](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L46) | Writes project settings. |
| `constant unset` | WRITE | Y | [cmd/mxcli/cmd_constant.go#L160](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L160) | |
| `constant list` | READ | Y | [cmd/mxcli/cmd_constant.go#L189](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L189) | |

### 2.7 `debug` subtree (Mendix runtime debugger over the project)

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `debug` | WRITE | Y | [cmd/mxcli/cmd_debug.go#L23](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L23) | Debugger parent. |
| `debug status` | READ | Y | [cmd/mxcli/cmd_debug.go#L43](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L43) | |
| `debug enable` / `disable` | WRITE | Y | [cmd/mxcli/cmd_debug.go#L65-L86](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L65-L86) | Toggles runtime debugger. |
| `debug activities <mf>` | READ | Y | [cmd/mxcli/cmd_debug.go#L105](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L105) | |
| `debug break` / `unbreak` | WRITE | Y | [cmd/mxcli/cmd_debug.go#L132-L185](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L132-L185) | Mutates breakpoint state. |
| `debug breaks` | READ | Y | [cmd/mxcli/cmd_debug.go#L222](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L222) | |
| `debug paused` | READ | Y | [cmd/mxcli/cmd_debug.go#L246](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L246) | |
| `debug inspect` | READ | Y | [cmd/mxcli/cmd_debug.go#L278](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L278) | |
| `debug step` / `continue` | WRITE | Y | [cmd/mxcli/cmd_debug.go#L307-L334](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L307-L334) | Mutates runtime state. |

### 2.8 `diag` subtree (local telemetry over mxcli's own logs)

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `diag` | READ | Y | [cmd/mxcli/diag.go#L24](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag.go#L24) | |
| `diag loop-report` | READ | Y | [cmd/mxcli/diag_loop_report.go#L582](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag_loop_report.go#L582) | |
| `diag session-report` | READ | Y | [cmd/mxcli/diag_session_report.go#L120](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag_session_report.go#L120) | Reads Claude Code transcripts. |

### 2.9 `docker` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `docker` | WRITE | Y | [cmd/mxcli/docker.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L15) | Docker/Podman parent. |
| `docker run` | WRITE | Y | [cmd/mxcli/docker.go#L54](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L54) | |
| `docker build` | WRITE | Y | [cmd/mxcli/docker.go#L108](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L108) | |
| `docker check` | READ | Y | [cmd/mxcli/docker.go#L172](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L172) | **Watch-out:** runs mx check on a container-local temp copy; writes Docker cache layers. |
| `docker init` | WRITE | Y | [cmd/mxcli/docker.go#L230](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L230) | |
| `docker up` / `down` | WRITE | Y | [cmd/mxcli/docker.go#L275-L323](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L275-L323) | |
| `docker logs` | READ | Y | [cmd/mxcli/docker.go#L354](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L354) | |
| `docker status` | READ | Y | [cmd/mxcli/docker.go#L387](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L387) | |
| `docker reload` | WRITE | Y | [cmd/mxcli/docker.go#L415](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L415) | |
| `docker shell` | WRITE | Y | [cmd/mxcli/docker.go#L478](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L478) | |

### 2.10 `eval` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `eval` | READ | Y | [cmd/mxcli/cmd_eval.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L17) | Parent. |
| `eval check <file>` | WRITE | Y | [cmd/mxcli/cmd_eval.go#L45](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L45) | Executes evals, may write reports under `-o`. |
| `eval list <file>` | READ | Y | [cmd/mxcli/cmd_eval.go#L238](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L238) | |
| `eval run <file>` | WRITE | Y | [cmd/mxcli/cmd_eval_run.go#L19](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval_run.go#L19) | Spawns Claude Code headless; writes transcripts. |

### 2.11 `fix` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `fix` | WRITE | Y | [cmd/mxcli/cmd_fix.go#L26-L95](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix.go#L26-L95) | Runs Mendix's own tooling then rewrites the `.mpr`. |
| `fix design-properties` | WRITE | Y | [cmd/mxcli/cmd_fix.go#L41](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix.go#L41) | |
| `fix widgets` | WRITE | Y | [cmd/mxcli/cmd_fix.go#L65](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix.go#L65) | |
| `fix hashes` | WRITE | Y | [cmd/mxcli/cmd_fix_hashes.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix_hashes.go#L22) | |
| `fix property-sets` | WRITE | Y | [cmd/mxcli/cmd_fix_property_sets.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix_property_sets.go#L22) | |

### 2.12 `git` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `git` | WRITE | Y | [cmd/mxcli/cmd_git.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_git.go#L17) | |
| `git note [<commit>...]` | WRITE | Y | [cmd/mxcli/cmd_git.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_git.go#L22) | Writes git notes. |

### 2.13 `layout` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `layout` | READ | Y | [cmd/mxcli/cmd_layout.go#L37](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout.go#L37) | Default lists; subcommands below. |
| `layout flows [Module.Flow ...]` | READ | Y | [cmd/mxcli/cmd_layout_flows.go#L29](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout_flows.go#L29) | **Watch-out:** catalog cache write. |

### 2.14 `log` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `log` | WRITE | Y | [cmd/mxcli/cmd_log.go#L34](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L34) | Runtime log-level control. |
| `log list` | READ | Y | [cmd/mxcli/cmd_log.go#L78](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L78) | |
| `log set <node> <level>` | WRITE | Y | [cmd/mxcli/cmd_log.go#L115](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L115) | Mutates runtime log config. |

### 2.15 `marketplace` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `marketplace` | READ | Y | [cmd/mxcli/cmd_marketplace.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L22) | |
| `marketplace search` | READ | Y | [cmd/mxcli/cmd_marketplace.go#L35](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L35) | |
| `marketplace info` | READ | Y | [cmd/mxcli/cmd_marketplace.go#L50](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L50) | |
| `marketplace versions` | READ | Y | [cmd/mxcli/cmd_marketplace.go#L59](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L59) | |
| `marketplace download` | WRITE | Y | [cmd/mxcli/cmd_marketplace.go#L69](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L69) | Writes `.mpk` to disk. |
| `marketplace install` | WRITE | Y | [cmd/mxcli/cmd_marketplace_install.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_install.go#L25) | Rewrites `.mpr`. |
| `marketplace update` | WRITE | Y | [cmd/mxcli/cmd_marketplace_update.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_update.go#L17) | Rewrites `.mpr`. |
| `marketplace diff` | READ | Y | [cmd/mxcli/cmd_marketplace_diff.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_diff.go#L18) | |

### 2.16 `mcp` subtree (CLIENT to Studio Pro, not server)

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `mcp` | READ | Y | [cmd/mxcli/mcp.go#L13-L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/mcp.go#L13-L18) | mxcli acts as an **MCP client** to a running Studio Pro's embedded MCP server (via `--mcp` URL). mxcli does NOT serve MCP (see §5). |
| `mcp capabilities` | READ | Y | [cmd/mxcli/mcp.go#L20-L51](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/mcp.go#L20-L51) | Prints what the server can author. |

### 2.17 `playwright` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `playwright` | WRITE | Y | [cmd/mxcli/cmd_playwright.go#L19](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L19) | Parent. |
| `playwright verify` | WRITE | Y | [cmd/mxcli/cmd_playwright.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L25) | Writes traces/screenshots. |
| `playwright open [url]` | WRITE | Y | [cmd/mxcli/cmd_playwright.go#L112](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L112) | Opens persistent browser context. |
| `playwright status` | READ | Y | [cmd/mxcli/cmd_playwright.go#L143](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L143) | |
| `playwright close` | WRITE | Y | [cmd/mxcli/cmd_playwright.go#L154](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L154) | |
| `playwright check` | WRITE | Y | [cmd/mxcli/cmd_playwright.go#L166](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L166) | Writes artefacts. |

### 2.18 `run` subtree (lifecycle on top of `run`)

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `run status` | READ | Y | [cmd/mxcli/cmd_run_lifecycle.go#L60](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L60) | |
| `run stop` | WRITE | Y | [cmd/mxcli/cmd_run_lifecycle.go#L79](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L79) | |
| `run wait` | READ | Y | [cmd/mxcli/cmd_run_lifecycle.go#L100](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L100) | |
| `run restart` | WRITE | Y | [cmd/mxcli/cmd_run_lifecycle.go#L137](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L137) | |

### 2.19 `setup` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `setup` | WRITE | Y | [cmd/mxcli/setup.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/setup.go#L18) | |
| `setup mxbuild` | WRITE | Y | [cmd/mxcli/setup.go#L37](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/setup.go#L37) | Downloads mxbuild under `~/.mxcli/`. |
| `setup mxruntime` | WRITE | Y | [cmd/mxcli/setup.go#L146](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/setup.go#L146) | Downloads runtime. |
| `setup mxcli` | WRITE | Y | [cmd/mxcli/setup.go#L282](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/setup.go#L282) | Self-updates. |

### 2.20 `skill` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `skill` | READ | Y | [cmd/mxcli/cmd_skill.go#L40](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L40) | |
| `skill list` | READ | Y | [cmd/mxcli/cmd_skill.go#L51](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L51) | |
| `skill add <pack>` | WRITE | Y | [cmd/mxcli/cmd_skill.go#L97](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L97) | Writes skill files. |
| `skill remove <pack>` | WRITE | Y | [cmd/mxcli/cmd_skill.go#L243](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L243) | |
| `skill upgrade [pack]` | WRITE | Y | [cmd/mxcli/cmd_skill.go#L263](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L263) | |

### 2.21 `theme` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `theme` | WRITE | Y | [cmd/mxcli/cmd_theme.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L18) | |
| `theme list` | READ | Y | [cmd/mxcli/cmd_theme.go#L59](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L59) | |
| `theme show` | READ | Y | [cmd/mxcli/cmd_theme.go#L100](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L100) | |
| `theme create` | WRITE | Y | [cmd/mxcli/cmd_theme.go#L167](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L167) | |
| `theme apply` | WRITE | Y | [cmd/mxcli/cmd_theme.go#L282](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L282) | |
| `theme remove` | WRITE | Y | [cmd/mxcli/cmd_theme.go#L362](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L362) | |
| `theme switcher` | WRITE | Y | [cmd/mxcli/cmd_theme.go#L407](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L407) | |
| `theme switcher install` | WRITE | Y | [cmd/mxcli/cmd_theme.go#L425](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L425) | |

### 2.22 `widget` subtree

| Command | Class | Verified | Source | Notes |
|---|---|---|---|---|
| `widget` | WRITE | Y | [cmd/mxcli/cmd_widget.go#L20](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L20) | |
| `widget extract` | WRITE | Y | [cmd/mxcli/cmd_widget.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L25) | |
| `widget list` | READ | Y | [cmd/mxcli/cmd_widget.go#L42](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L42) | |
| `widget init` | WRITE | Y | [cmd/mxcli/cmd_widget.go#L49](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L49) | |
| `widget docs` | READ | Y | [cmd/mxcli/cmd_widget.go#L69](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L69) | |
| `widget describe` | READ | Y | [cmd/mxcli/cmd_widget_describe.go#L46](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget_describe.go) | |
| `widget sync` | WRITE | Y | [cmd/mxcli/cmd_widget_sync.go#L68](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget_sync.go) | Rewrites the `.mpr` to resync widget schemas. |

## 3. Watch-out: looks READ but has side-effects

- **`check` (several-file form)** creates a scratch-copy project in `os.TempDir()` via
  `scriptdiff.NewScratch` (`mdl/scriptdiff/scriptdiff.go#L176`) and applies each file to it
  as the set is checked, deleting the copy on return. The original `.mpr` is never
  touched. [cmd_check.go#L558-L594](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check.go#L558-L594).
- **Implicit catalog cache write (`.mxcli/catalog.db`).** Any command that calls
  `ensureCatalog(ctx, …)` writes to `<project-dir>/.mxcli/catalog.db` even when the
  invocation looks read-only. The cache path is computed in
  [mdl/executor/cmd_catalog.go#L372-L380](https://github.com/mendixlabs/mxcli/blob/v0.26.0/mdl/executor/cmd_catalog.go#L372-L380).
  Commands that reach `ensureCatalog`: `describe`, `show` (some targets), `search`,
  `callers`, `callees`, `refs`, `impact`, `structure`, `context`, `lint`, `report`,
  `graph-report`, `project-tree`, `layout flows`, several MDL statements run through
  `exec`/`-c`. If a policy is strict about any filesystem write, these are
  side-effecting. If the policy is only about `.mpr` writes, they are safe.
- **`docker check`** runs `mx check` on a temp copy, but still writes Docker cache
  layers and container state. See [docker.go#L172](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L172) and `cmd/mxcli/docker/check.go`.
- **`report` / `graph-report`** force a `REFRESH CATALOG FULL` before scoring, so the
  `.mxcli/catalog.db` write is unavoidable even without `--output`. See
  [cmd_report.go#L78-L80](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_report.go#L78-L80).
- **`search`** likewise ensures the catalog exists.
- **`fmt -w`** rewrites files in place; `fmt` without `-w` is READ.

## 4. Claude Code target (`init` and `add-tool`)

### 4.1 `init` vs `add-tool` — distinct commands

They are **distinct**, not wrappers.

- `init` ([cmd/mxcli/init.go#L65-L686](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L65-L686))
  does the full project bootstrap: `.ai-context/skills/`,
  `.ai-context/examples/`, `.claude/commands/`, `.claude/lint-rules/`,
  `.claude/lint-config.yaml`, `.claude/skills/` (via `syncAIContextSkills`),
  `.claude/skills/<companion>/` (via `syncCompanion`), the Claude Code mod pack,
  `mdlsource/` with a README, the `.gitignore` top-up, the devcontainer files
  (when selected), and then the per-tool entries from `SupportedTools`.
- `add-tool` ([cmd/mxcli/cmd_add_tool.go#L16-L277](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_add_tool.go#L16-L277))
  writes **only** the `toolConfig.Files` for the named tool and skips existing
  files; it does not touch `.ai-context/`, does not create the companion mod,
  does not seed `lint-config.yaml`, and does not create `mdlsource/`. The
  epilogue even warns "Run 'mxcli init' first to create universal documentation."
  (`cmd_add_tool.go#L135`). The `opencode` and `vibe` tool entries have extra
  per-tool skill-sync branches, but Claude Code's entry does not.

So: `init` includes everything `add-tool claude` does **plus** the universal
scaffolding.

### 4.2 What the Claude Code target writes

The `SupportedTools["claude"]` entry
([cmd/mxcli/tool_templates.go#L28-L41](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/tool_templates.go#L28-L41))
lists two files:

```go
"claude": {
    Name:        "Claude Code",
    Description: "Claude Code with skills and commands",
    Files: []ToolFile{
        {Path: ".claude/settings.json", Content: generateClaudeSettings},
        {Path: "CLAUDE.md",             Content: generateClaudeMD},
    },
},
```

In addition, `init` writes (for the Claude Code target):

- `.claude/commands/*.md` — the embedded `commands/` tree
  ([init.go#L340-L364](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L340-L364), fed by `commandsFS` in `cmd/mxcli/skills_content.go#L51-L52`).
- `.claude/lint-rules/*.star` — the embedded `lint-rules/` tree
  ([init.go#L366-L389](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L366-L389), fed by `lintRulesFS` in `skills_content.go#L55-L57`).
- `.claude/lint-config.yaml` — via `writeDefaultLintConfig`
  ([init.go#L646-L686](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L646-L686), filename at `init.go#L659`).
- `.claude/skills/<name>/SKILL.md` and the "mxcli companion" plugin folder
  in `.claude/skills/<companion>/` — via `syncAIContextSkills` and
  `syncCompanion` ([init.go#L280-L299](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L280-L299)).
- `AGENTS.md` — the universal doc, same body as `CLAUDE.md`
  (`UniversalFiles` in [tool_templates.go#L120-L125](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/tool_templates.go#L120-L125);
  `generateProjectAIMD` returns `generateClaudeMD(...)` at
  [tool_templates.go#L438-L440](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/tool_templates.go#L438-L440)).

### 4.3 `.claude/settings.json` — exact content

`generateClaudeSettings` returns the constant `settingsJSON`
([cmd/mxcli/skills_content.go#L65-L79](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/skills_content.go#L65-L79)):

```json
{
  "permissions": {
    "allow": [
      "Bash(mxcli:*)",
      "Bash(./mxcli:*)",
      "Bash(./mxcli *)",
      "Bash(playwright-cli:*)",
      "Bash(playwright-cli *)"
    ]
  },
  "env": {
    "MXCLI_QUIET": "1"
  }
}
```

Observations:

- **`permissions.allow` is present** (5 entries: three mxcli variants, two
  playwright-cli variants). There is no `permissions.deny`.
- **No `hooks` block.** mxcli v0.26.0 does NOT configure Claude Code
  SessionStart/PreToolUse/PostToolUse hooks. The "SessionStart refresh"
  described in `init_tooling_sync.go#L218-L269` is a feature mxcli expects
  the host project to wire in itself (the comment at `init_tooling_sync.go#L23`
  references `mxcli-formula1 §16` for the bootstrap script).
- `env.MXCLI_QUIET: "1"` is set, which suppresses the warning banner mxcli
  prints by default (`cmd/mxcli/main.go#L29-L34`, `#L70-L73`).

### 4.4 BEGIN/END markers in `AGENTS.md` and `CLAUDE.md`

The owned-doc writer uses HTML-comment markers
([cmd/mxcli/init_tooling_sync.go#L28-L32](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init_tooling_sync.go#L28-L32)):

```
<!-- mxcli:begin — generated by mxcli and refreshed by 'mxcli init --sync-skills'. Edit outside these markers; anything between them is replaced. -->
…mxcli-generated body…
<!-- mxcli:end -->
```

- Begin line is matched by **prefix only** (`mxcliSectionBeginPrefix = "<!-- mxcli:begin"`),
  so the exact wording after it can change without orphaning files written by
  older binaries ([init_tooling_sync.go#L71](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init_tooling_sync.go#L71)).
- `wrapMxcliSection` is at [init_tooling_sync.go#L58-L64](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init_tooling_sync.go#L58-L64);
  `mergeMxcliSection` at [#L70-L87](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init_tooling_sync.go#L70-L87).
- Only `CLAUDE.md` and `AGENTS.md` go through these markers; `.claude/settings.json`
  is a plain overwrite (actually: `add-tool` *skips* existing files; `init` writes
  `.claude/settings.json` through `writeOwnedDoc` only if it is in `ownedDocs()`,
  which it is not — `ownedDocs` returns the `CLAUDE.md` entry from `SupportedTools["claude"].Files`
  plus `UniversalFiles` only, so `.claude/settings.json` is written once and never
  refreshed).

## 5. MCP server mode — ABSENT

**Verified absent at v0.26.0.** The `mcp` subcommand in
[cmd/mxcli/mcp.go#L13-L56](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/mcp.go#L13-L56)
is strictly an **MCP CLIENT** that connects to a running Studio Pro's embedded
MCP server (via the `--mcp <url>` persistent flag). Its only subcommand is
`mcp capabilities`, which prints what the connected server can author.

The MCP client backend code lives in `mdl/backend/mcp/` and the probe utility
in `cmd/mcpprobe/`. There is no `serve`-style command that exposes mxcli
functionality to an MCP client, no `stdio`/`jsonrpc` transport implementation
in the command tree, and no `mxcli serve mcp` or similar.

(`mxcli serve`, [cmd/mxcli/serve.go#L37-L72](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/serve.go#L37-L72),
is an unrelated HTTP server that renders a project treemap in a browser.)

If a future tag adds MCP server mode, re-run this section.

## 6. Studio Pro lock file — reconfirmed

- Lock filename: **`<project>.mpr.lock`**, located beside the `.mpr`
  (lower-cased, matching Studio Pro's own `.gitignore` convention).
- Defined and detected in
  [modelsdk/mpr/studiopro_lock.go#L20-L89](https://github.com/mendixlabs/mxcli/blob/v0.26.0/modelsdk/mpr/studiopro_lock.go#L20-L89).
  `StudioProLockFile(mprPath string) (string, time.Time)` at `#L58`.
- Env-var override: **`MXCLI_ALLOW_STUDIO_PRO_OPEN`** (set to any non-empty
  value) — constant `AllowStudioProOpenEnv` at
  [modelsdk/mpr/studiopro_lock.go#L38](https://github.com/mendixlabs/mxcli/blob/v0.26.0/modelsdk/mpr/studiopro_lock.go#L38).
- Flag overrides on `exec`: `--force` sets `mmpr.AllowWritesWhileStudioProOpen = true`
  for the process ([cmd/mxcli/cmd_exec.go#L65-L71](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go#L65-L71),
  flag registered at [#L157-L158](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go#L157-L158)).
- The behaviour: reads are never refused; writes are refused with an error
  pointing at the lock file; `--force`/env var warns but writes anyway
  (user accepts the risk Studio Pro's next save will silently discard the
  change).
- `--no-check` is a separate flag ([cmd_exec.go#L153-L154](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go#L153-L154))
  that skips `exec`'s pre-flight semantic validation; it does **not** bypass
  the Studio Pro lock. For `diff`, `--no-check` is at
  [main.go#L356-L359](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/main.go#L356-L359).

## 7. Remaining UNVERIFIED items

- **Exact Studio Pro version floor.** The lock-file check is present at v0.26.0,
  but the oldest Studio Pro version against which mxcli writes have been
  tested is not stated in source. Still UNVERIFIED pending maintainer
  confirmation.
- **`mxcli --help` and per-command `--help` output.** Not captured on this
  host; the inventory was derived from source. See
  [docs/research/mxcli-help/v0.26.0/README.md](mxcli-help/v0.26.0/README.md)
  for the capture snippet.
- **Catalog build timing / cost per command.** Confirmed each read command
  can trigger `ensureCatalog`, but the exact first-run cost and when the
  cache is reused vs rebuilt was not measured here.

## 8. Verification trail

Files read in `.research/mxcli-v0.26.0/` (local clone pinned at SHA
`12ce281622a1a78ebb6737e61fe6b5ea78c59e45`):

- `cmd/mxcli/main.go` (root, flag registrations, `rootCmd.AddCommand` list)
- `cmd/mxcli/cmd_show.go`, `cmd_describe.go`, `cmd_check.go`,
  `cmd_check_post_migration.go`, `cmd_diff.go`, `cmd_exec.go`,
  `cmd_fmt.go`, `cmd_fix.go`, `cmd_fix_hashes.go`,
  `cmd_fix_property_sets.go`, `cmd_rename.go`, `cmd_lint.go`,
  `cmd_report.go`, `cmd_graph_report.go`, `cmd_query.go`,
  `cmd_catalog.go`, `cmd_changelog.go`, `cmd_constant.go`,
  `cmd_debug.go`, `cmd_eval.go`, `cmd_eval_run.go`, `cmd_extract_templates.go`,
  `cmd_git.go`, `cmd_help_code.go`, `cmd_layout.go`, `cmd_layout_flows.go`,
  `cmd_log.go`, `cmd_marketplace.go`, `cmd_marketplace_diff.go`,
  `cmd_marketplace_install.go`, `cmd_marketplace_update.go`,
  `cmd_new.go`, `cmd_playwright.go`, `cmd_rename.go`, `cmd_run.go`,
  `cmd_run_lifecycle.go`, `cmd_skill.go`, `cmd_sql.go`,
  `cmd_sync_java_deps.go`, `cmd_test_run.go`, `cmd_theme.go`,
  `cmd_tui.go`, `cmd_tunnelhub.go`, `cmd_version.go`, `cmd_widget.go`,
  `cmd_widget_describe.go`, `cmd_widget_sync.go`, `cmd_bson.go`,
  `cmd_bson_dump.go`, `cmd_bson_discover.go`, `cmd_add_tool.go`,
  `cmd_auth.go`, `cmd_auth_hub.go`, `cmd_brain.go`
- `cmd/mxcli/init.go`, `init_tooling_sync.go`, `tool_templates.go`,
  `skills_content.go`
- `cmd/mxcli/serve.go`, `mcp.go`, `docker.go`, `docker_oql.go`, `help.go`,
  `lsp.go`, `setup.go`, `project_tree.go`, `diag.go`,
  `diag_loop_report.go`, `diag_session_report.go`
- `modelsdk/mpr/studiopro_lock.go` (lock-file API)
- `mdl/executor/cmd_catalog.go#L370-L410` (catalog cache path and
  `ensureCatalog` usage)
- `mdl/scriptdiff/scriptdiff.go#L170-L180` (scratch-copy construction)

Grep queries used:

- `AddCommand\(` across `cmd/mxcli/` to enumerate registrations.
- `Use:\s*"` across `cmd/mxcli/` to pick up each command's `Use` string.
- `StudioProLockFile|\.mpr\.lock|MXCLI_ALLOW_STUDIO_PRO_OPEN` (lock details).
- `SupportedTools`, `settingsJSON`, `generateClaudeMD`, `wrapMxcliSection`,
  `mxcliSectionBegin` (Claude Code target).
- `mcp serve|mcpServerCmd|jsonrpc|stdio` (MCP server mode) — nothing
  matched in the command tree.
- `ensureCatalog|catalog\.db|REFRESH CATALOG` (implicit cache writes).
