# mxcli inventory (v0.26.0)

Last reviewed: 2026-10-21. Upstream: `mendixlabs/mxcli` at tag
[`v0.26.0`](https://github.com/mendixlabs/mxcli/tree/v0.26.0). Command
classes were derived by reading the Go source in a local clone of that tag at
SHA `12ce281622a1a78ebb6737e61fe6b5ea78c59e45`; which paths exist was
checked against the released binary (ADR-0036, §8.1). The command tables in
§2 are generated from `policy/mxcli-commands.json` (ADR-0035). Anything still
UNVERIFIED (see section 7) is treated as **WRITE** by the policy guard
(ADR-0007).

## 1. Version used

- Tag: [`v0.26.0`](https://github.com/mendixlabs/mxcli/tree/v0.26.0).
- Resolved SHA: `12ce281622a1a78ebb6737e61fe6b5ea78c59e45`.
- Permalink base: `https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/<path>#L<line>` (the `/v0.26.0/` tag form also resolves and is used below for readability).
- **Newer tag out of scope for this pin:** v0.27.0 (released 2026-10-15). ADR-0013 keeps the project pinned at v0.26.0; any upgrade requires re-running this inventory before relying on it.

## 2. Command tree

Cobra command registrations are rooted in `cmd/mxcli/main.go` (lines 437–462)
and in each file's own `init()` via `rootCmd.AddCommand(...)`. The tables
below group commands by their parent and are **generated** from
`policy/mxcli-commands.json`, the source of record, by
`.github/scripts/render_mxcli_inventory.py` (ADR-0035). Edit the JSON, then
re-run the script; a unit test fails on drift. "Verified" means the
command's `Short`/`Long` and `RunE`/`Run` were read at this SHA and its
write paths chased.

Which paths exist is decided by the released v0.26.0 binary's `--help` tree
(CI job `mxcli command-tree check`); their class is decided by the source
(ADR-0036). Every path has its own row, including WRITE children of WRITE
parents. Rows may carry `hidden` or `build_condition` when a path is absent
from `--help`; none at v0.26.0 do (see §8).

<!-- BEGIN GENERATED from policy/mxcli-commands.json by .github/scripts/render_mxcli_inventory.py; do not edit -->

### 2.1 Root commands

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `help` | READ | Y | — | built-in cobra help |  |
| `version` | READ | Y | — | [cmd/mxcli/cmd_version.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_version.go#L17) | Prints build info. |
| `changelog` | READ | Y | — | [cmd/mxcli/cmd_changelog.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_changelog.go#L17) | Prints embedded CHANGELOG. |
| `syntax` | READ | Y | — | [cmd/mxcli/help.go#L17-L96](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/help.go#L17-L96) | MDL syntax reference from the embedded registry. |
| `show` | READ | Y | catalog | [cmd/mxcli/cmd_show.go#L13-L82](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_show.go#L13-L82) | Alias: list. Watch-out: may trigger implicit catalog cache build. |
| `list` | READ | Y | catalog | alias of show (cmd_show.go) | Dispatches to MDL `SHOW …`. **Watch-out:** can trigger implicit catalog build (see §3). |
| `describe` | READ | Y | catalog | [cmd/mxcli/cmd_describe.go#L18-L225](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_describe.go#L18-L225) | Watch-out: may build .mxcli/catalog.db. |
| `search` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L225-L290](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L225-L290) | Watch-out: builds .mxcli/catalog.db on first use. |
| `callers` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L15-L43](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L15-L43) | Runs MDL `SHOW CALLERS OF`. **Watch-out:** catalog cache write. |
| `callees` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L45-L73](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L45-L73) | Runs MDL `SHOW CALLEES OF`. **Watch-out:** catalog cache write. |
| `refs` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L75-L99](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L75-L99) | Runs MDL `SHOW REFERENCES TO`. **Watch-out:** catalog cache write. |
| `impact` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L101-L127](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L101-L127) | Runs MDL `SHOW IMPACT OF`. **Watch-out:** catalog cache write. |
| `structure` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L129-L172](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L129-L172) | Runs MDL `DESCRIBE STRUCTURE`. **Watch-out:** catalog cache write. |
| `context` | READ | Y | catalog | [cmd/mxcli/cmd_query.go#L174-L223](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go#L174-L223) | Runs MDL `DESCRIBE CONTEXT OF`. **Watch-out:** catalog cache write. |
| `check` | READ | Y | catalog, tempdir | [cmd/mxcli/cmd_check.go#L21-L595](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check.go#L21-L595) | Watch-out: multi-file form creates a temp scratch-copy via scriptdiff.NewScratch and may build .mxcli/catalog.db. The real .mpr is never modified. |
| `diff` | READ | Y | tempdir | [cmd/mxcli/cmd_diff.go#L19-L125](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_diff.go#L19-L125) | Watch-out: scratch-copy write to a temp dir, deleted on exit. |
| `diff-local` | READ | Y | — | [cmd/mxcli/cmd_diff.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_diff.go) | Git-ref diff (reads prior commits). |
| `lint` | READ | Y | catalog | [cmd/mxcli/cmd_lint.go#L19-L300](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_lint.go#L19-L300) | Watch-out: builds .mxcli/catalog.db. |
| `project-tree` | READ | Y | catalog | [cmd/mxcli/project_tree.go#L41](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/project_tree.go#L41) | Watch-out: likely catalog cache write. |
| `sql` | WRITE | Y | network | [cmd/mxcli/cmd_sql.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_sql.go#L16) | Reclassified WRITE (ADR-0014 reasoning): the user-supplied query reaches an external database and can mutate it (UPDATE/DELETE/DDL). The policy does not inspect the query, so classify at the command level. |
| `oql` | READ | Y | — | [cmd/mxcli/docker_oql.go#L14](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker_oql.go#L14) | OQL query runner (SELECT-shaped). |
| `exec` | WRITE | Y | files | [cmd/mxcli/cmd_exec.go#L17-L161](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go#L17-L161) | Executes MDL against the .mpr. Lock-file check via mmpr.StudioProLockFile(); --force bypasses lock; --no-check skips pre-flight validation. |
| `fmt` | WRITE | Y | files | [cmd/mxcli/cmd_fmt.go#L26](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fmt.go#L26) | `fmt -w` writes in place; `fmt` alone emits to stdout. |
| `rename` | WRITE | Y | files | [cmd/mxcli/cmd_rename.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_rename.go#L17) | Rewrites the `.mpr`. |
| `new` | WRITE | Y | files | [cmd/mxcli/cmd_new.go#L20](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_new.go#L20) | Creates a new project scaffold. |
| `init` | WRITE | Y | files | [cmd/mxcli/init.go#L65-L686](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/init.go#L65-L686) | Writes .ai-context/, .claude/, CLAUDE.md, AGENTS.md, lint-config, skills tree, lint-rules, companion mod, mdlsource/. Distinct from add-tool. |
| `add-tool` | WRITE | Y | files | [cmd/mxcli/cmd_add_tool.go#L16-L277](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_add_tool.go#L16-L277) | Writes tool-specific files from SupportedTools map. Claude Code target writes .claude/settings.json (permissions.allow + env.MXCLI_QUIET; no hooks) and CLAUDE.md. See docs/research/mxcli-inventory.md §4. |
| `report` | WRITE | Y | catalog, files | [cmd/mxcli/cmd_report.go#L18-L80](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_report.go#L18-L80) | Runs REFRESH CATALOG FULL (writes .mxcli/catalog.db); --output writes report file. |
| `graph-report` | WRITE | Y | catalog, files | [cmd/mxcli/cmd_graph_report.go#L21](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_graph_report.go#L21) | Catalog build + optional --output file. |
| `run` | WRITE | Y | process, files | [cmd/mxcli/cmd_run.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run.go#L18) | Boots the app locally; writes deployment artefacts, logs, lifecycle state. |
| `serve` | WRITE | Y | process, network | [cmd/mxcli/serve.go#L37-L72](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/serve.go#L37-L72) | HTTP visualization server; binds a port and builds catalog. Not MCP (see §5). |
| `lsp` | WRITE | Y | process | [cmd/mxcli/lsp.go#L24](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/lsp.go#L24) | Long-running Language Server over stdio. |
| `tui` | WRITE | Y | process | [cmd/mxcli/cmd_tui.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_tui.go#L15) | Interactive TUI; writes session state. |
| `test` | WRITE | Y | process, files | [cmd/mxcli/cmd_test_run.go#L15-L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_test_run.go#L15-L16) | Runs tests; boots runtime; writes deployment + logs. |
| `extract-templates` | WRITE | Y | files | [cmd/mxcli/cmd_extract_templates.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_extract_templates.go#L18) | Writes templates to disk. |
| `sync-java-deps` | WRITE | Y | files | [cmd/mxcli/cmd_sync_java_deps.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_sync_java_deps.go#L15) | Rewrites project Java deps. |
| `tunnel-hub` | WRITE | Y | process, network | [cmd/mxcli/cmd_tunnelhub.go#L25-L223](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_tunnelhub.go#L25-L223) | Long-running hub service; writes PID/state. Linux-only. |
| `auth` | WRITE | Y | credentials | [cmd/mxcli/cmd_auth.go#L28](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L28) | Parent WRITE because login/logout mutate credential store. Specific READ subcommands below. |
| `brain` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L25) | Research "brain" store. |
| `bson` | READ | Y | — | [cmd/mxcli/cmd_bson.go#L8](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson.go#L8) |  |
| `catalog` | READ | Y | network | [cmd/mxcli/cmd_catalog.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L16) | External Mendix Catalog service (catalog.mendix.com), NOT the local MDL `CATALOG` keyword. External Mendix Catalog service, NOT the local MDL CATALOG keyword. |
| `constant` | WRITE | Y | files | [cmd/mxcli/cmd_constant.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L18) |  |
| `debug` | WRITE | Y | network | [cmd/mxcli/cmd_debug.go#L23](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L23) | Mendix runtime debugger over the project. Debugger parent. |
| `diag` | READ | Y | — | [cmd/mxcli/diag.go#L24](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag.go#L24) | Local telemetry over mxcli's own logs. |
| `docker` | WRITE | Y | docker | [cmd/mxcli/docker.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L15) | Docker/Podman parent. |
| `eval` | READ | Y | — | [cmd/mxcli/cmd_eval.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L17) | Parent. |
| `fix` | WRITE | Y | files | [cmd/mxcli/cmd_fix.go#L26-L95](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix.go#L26-L95) | Runs Mendix's own tooling then rewrites the `.mpr`. |
| `git` | WRITE | Y | files | [cmd/mxcli/cmd_git.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_git.go#L17) |  |
| `layout` | READ | Y | catalog | [cmd/mxcli/cmd_layout.go#L37](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout.go#L37) | Default lists; subcommands below. |
| `log` | WRITE | Y | network | [cmd/mxcli/cmd_log.go#L34](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L34) | Runtime log-level control. |
| `marketplace` | READ | Y | network | [cmd/mxcli/cmd_marketplace.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L22) |  |
| `mcp` | READ | Y | network | [cmd/mxcli/mcp.go#L13-L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/mcp.go#L13-L18) | mxcli acts as MCP CLIENT to Studio Pro's embedded MCP server. NOT an MCP server (confirmed in inventory §5). |
| `playwright` | WRITE | Y | process, files | [cmd/mxcli/cmd_playwright.go#L19](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L19) | Parent. |
| `setup` | WRITE | Y | network, files | [cmd/mxcli/setup.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/setup.go#L18) |  |
| `skill` | READ | Y | — | [cmd/mxcli/cmd_skill.go#L40](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L40) |  |
| `theme` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L18) |  |
| `widget` | WRITE | Y | files | [cmd/mxcli/cmd_widget.go#L20](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L20) |  |
| `completion` | READ | Y | — | cobra built-in | Prints a shell completion script to stdout (cobra default command). |

### 2.2 `auth` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `auth` | WRITE | Y | credentials | [cmd/mxcli/cmd_auth.go#L28](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L28) | Parent WRITE because login/logout mutate credential store. Specific READ subcommands below. |
| `auth login` | WRITE | Y | credentials, network | [cmd/mxcli/cmd_auth.go#L46](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L46) | Writes `~/.mxcli/auth.json`. |
| `auth logout` | WRITE | Y | credentials | [cmd/mxcli/cmd_auth.go#L62](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L62) | Rewrites credential store. |
| `auth status` | READ | Y | — | [cmd/mxcli/cmd_auth.go#L68](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L68) |  |
| `auth list` | READ | Y | — | [cmd/mxcli/cmd_auth.go#L74](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go#L74) |  |
| `auth hub` | WRITE | Y | credentials | [cmd/mxcli/cmd_auth_hub.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go) | Parent WRITE because login/logout mutate credential store. |
| `auth hub login` | WRITE | Y | credentials, network | [cmd/mxcli/cmd_auth_hub.go#L39](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go#L39) | Writes credential store. |
| `auth hub status` | READ | Y | network | [cmd/mxcli/cmd_auth_hub.go#L45](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go#L45) |  |
| `auth hub logout` | WRITE | Y | credentials | [cmd/mxcli/cmd_auth_hub.go#L51](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go#L51) |  |

### 2.3 `brain` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `brain` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L25) | Research "brain" store. |
| `brain init` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L65](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L65) | Creates store under `.claude/brain/`. |
| `brain capture` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L85](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L85) | Writes a shard. |
| `brain staged` | READ | Y | — | [cmd/mxcli/cmd_brain.go#L129](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L129) | Lists staged shards. |
| `brain promote` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L191](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L191) |  |
| `brain drop` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L222](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L222) |  |
| `brain show` | READ | Y | — | [cmd/mxcli/cmd_brain.go#L248](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L248) |  |
| `brain resolve` | WRITE | Y | files | [cmd/mxcli/cmd_brain.go#L288](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L288) |  |
| `brain plan` | READ | Y | — | [cmd/mxcli/cmd_brain.go#L321](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L321) |  |
| `brain brief` | READ | Y | — | [cmd/mxcli/cmd_brain.go#L391](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L391) |  |
| `brain check` | READ | Y | — | [cmd/mxcli/cmd_brain.go#L455](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go#L455) |  |

### 2.4 `bson` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `bson` | READ | Y | — | [cmd/mxcli/cmd_bson.go#L8](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson.go#L8) |  |
| `bson dump` | READ | Y | — | [cmd/mxcli/cmd_bson_dump.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson_dump.go#L18) | Dumps a unit to stdout. |
| `bson discover` | READ | Y | — | [cmd/mxcli/cmd_bson_discover.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson_discover.go#L16) |  |

### 2.5 `catalog` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `catalog` | READ | Y | network | [cmd/mxcli/cmd_catalog.go#L16](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L16) | External Mendix Catalog service (catalog.mendix.com), NOT the local MDL `CATALOG` keyword. External Mendix Catalog service, NOT the local MDL CATALOG keyword. |
| `catalog search` | READ | Y | network | [cmd/mxcli/cmd_catalog.go#L33-L116](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L33-L116) | Remote HTTP read. |
| `catalog show` | READ | Y | network | [cmd/mxcli/cmd_catalog.go#L46-L185](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go#L46-L185) | Remote HTTP read. |

### 2.6 `completion` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `completion` | READ | Y | — | cobra built-in | Prints a shell completion script to stdout (cobra default command). |
| `completion bash` | READ | Y | — | cobra built-in | Prints the bash completion script. |
| `completion fish` | READ | Y | — | cobra built-in | Prints the fish completion script. |
| `completion powershell` | READ | Y | — | cobra built-in | Prints the PowerShell completion script. |
| `completion zsh` | READ | Y | — | cobra built-in | Prints the zsh completion script. |

### 2.7 `constant` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `constant` | WRITE | Y | files | [cmd/mxcli/cmd_constant.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L18) |  |
| `constant set` | WRITE | Y | files | [cmd/mxcli/cmd_constant.go#L46](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L46) | Writes project settings. |
| `constant unset` | WRITE | Y | files | [cmd/mxcli/cmd_constant.go#L160](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L160) |  |
| `constant list` | READ | Y | — | [cmd/mxcli/cmd_constant.go#L189](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go#L189) |  |

### 2.8 `debug` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `debug` | WRITE | Y | network | [cmd/mxcli/cmd_debug.go#L23](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L23) | Mendix runtime debugger over the project. Debugger parent. |
| `debug status` | READ | Y | — | [cmd/mxcli/cmd_debug.go#L43](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L43) |  |
| `debug activities` | READ | Y | — | [cmd/mxcli/cmd_debug.go#L105](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L105) |  |
| `debug breaks` | READ | Y | — | [cmd/mxcli/cmd_debug.go#L222](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L222) |  |
| `debug paused` | READ | Y | — | [cmd/mxcli/cmd_debug.go#L246](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L246) |  |
| `debug inspect` | READ | Y | — | [cmd/mxcli/cmd_debug.go#L278](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go#L278) |  |
| `debug enable` | WRITE | Y | network, files | [cmd/mxcli/cmd_debug.go#L65](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_debug.go#L65) | Enables the runtime debugger and starts a session; caches the session token in <project>/.mxcli/debug-session.token (cmd_debug.go#L466). |
| `debug disable` | WRITE | Y | network, files | [cmd/mxcli/cmd_debug.go#L86](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_debug.go#L86) | Disables the runtime debugger and clears the cached session. |
| `debug break` | WRITE | Y | network | [cmd/mxcli/cmd_debug.go#L132](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_debug.go#L132) | Sets a breakpoint in the running runtime. |
| `debug unbreak` | WRITE | Y | network | [cmd/mxcli/cmd_debug.go#L185](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_debug.go#L185) | Clears a breakpoint in the running runtime. |
| `debug step` | WRITE | Y | network | [cmd/mxcli/cmd_debug.go#L307](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_debug.go#L307) | Advances a paused microflow; mutates runtime state. |
| `debug continue` | WRITE | Y | network | [cmd/mxcli/cmd_debug.go#L334](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_debug.go#L334) | Resumes a paused microflow; mutates runtime state. |

### 2.9 `diag` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `diag` | READ | Y | — | [cmd/mxcli/diag.go#L24](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag.go#L24) | Local telemetry over mxcli's own logs. |
| `diag loop-report` | READ | Y | — | [cmd/mxcli/diag_loop_report.go#L582](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag_loop_report.go#L582) |  |
| `diag session-report` | READ | Y | — | [cmd/mxcli/diag_session_report.go#L120](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/diag_session_report.go#L120) | Reads Claude Code transcripts. |

### 2.10 `docker` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `docker` | WRITE | Y | docker | [cmd/mxcli/docker.go#L15](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L15) | Docker/Podman parent. |
| `docker check` | READ | Y | docker, tempdir | [cmd/mxcli/docker.go#L172](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L172) | Watch-out: writes Docker cache layers and container state. |
| `docker logs` | READ | Y | — | [cmd/mxcli/docker.go#L354](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L354) |  |
| `docker status` | READ | Y | — | [cmd/mxcli/docker.go#L387](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/docker.go#L387) |  |
| `docker run` | WRITE | Y | docker, network, files, process | [cmd/mxcli/docker.go#L54](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L54) | Downloads MxBuild and runtime, initialises the stack, builds the PAD package and starts it. |
| `docker build` | WRITE | Y | docker, files, tempdir | [cmd/mxcli/docker.go#L108](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L108) | Builds a Portable App Distribution package. |
| `docker init` | WRITE | Y | files | [cmd/mxcli/docker.go#L230](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L230) | Writes .docker/ (docker-compose.yml, .env.example, .env) next to the .mpr. |
| `docker up` | WRITE | Y | docker, process | [cmd/mxcli/docker.go#L275](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L275) | Starts the Docker Compose stack. |
| `docker down` | WRITE | Y | docker, process | [cmd/mxcli/docker.go#L323](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L323) | Stops the Docker Compose stack. |
| `docker reload` | WRITE | Y | docker, files, network | [cmd/mxcli/docker.go#L415](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L415) | Builds and hot-reloads the model via the M2EE admin API. |
| `docker shell` | WRITE | Y | docker, process | [cmd/mxcli/docker.go#L478](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/docker.go#L478) | Opens an interactive shell in the Mendix container. |

### 2.11 `eval` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `eval` | READ | Y | — | [cmd/mxcli/cmd_eval.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L17) | Parent. |
| `eval list` | READ | Y | — | [cmd/mxcli/cmd_eval.go#L238](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L238) |  |
| `eval check` | WRITE | Y | files | [cmd/mxcli/cmd_eval.go#L45](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go#L45) | Executes evals, may write reports under `-o`. |
| `eval run` | WRITE | Y | files, process | [cmd/mxcli/cmd_eval_run.go#L19](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval_run.go#L19) | Spawns Claude Code headless; writes transcripts. |

### 2.12 `fix` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `fix` | WRITE | Y | files | [cmd/mxcli/cmd_fix.go#L26-L95](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix.go#L26-L95) | Runs Mendix's own tooling then rewrites the `.mpr`. |
| `fix design-properties` | WRITE | Y | files, process | [cmd/mxcli/cmd_fix.go#L42](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_fix.go#L42) | Runs `mx rename-design-properties` and writes the renamed units back into the .mpr (clears CE6087). |
| `fix widgets` | WRITE | Y | files, process | [cmd/mxcli/cmd_fix.go#L66](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_fix.go#L66) | Runs `mx update-widgets` and writes the result back into the .mpr (clears CE0463). |
| `fix hashes` | WRITE | Y | files | [cmd/mxcli/cmd_fix_hashes.go#L22](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_fix_hashes.go#L22) | Verifies the MPR v2 ContentsHash index; with --repair rewrites it. Without --repair it only reports, but the class is per path, not per flag. |
| `fix property-sets` | WRITE | Y | files | [cmd/mxcli/cmd_fix_property_sets.go#L22](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_fix_property_sets.go#L22) | Rewrites stored units with Studio Pro's property names. |

### 2.13 `git` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `git` | WRITE | Y | files | [cmd/mxcli/cmd_git.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_git.go#L17) |  |
| `git note` | WRITE | Y | files | [cmd/mxcli/cmd_git.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_git.go#L22) | Writes git notes. |

### 2.14 `layout` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `layout` | READ | Y | catalog | [cmd/mxcli/cmd_layout.go#L37](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout.go#L37) | Default lists; subcommands below. |
| `layout flows` | READ | Y | catalog | [cmd/mxcli/cmd_layout_flows.go#L29](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout_flows.go#L29) | **Watch-out:** catalog cache write. |

### 2.15 `log` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `log` | WRITE | Y | network | [cmd/mxcli/cmd_log.go#L34](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L34) | Runtime log-level control. |
| `log list` | READ | Y | — | [cmd/mxcli/cmd_log.go#L78](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L78) |  |
| `log set` | WRITE | Y | network | [cmd/mxcli/cmd_log.go#L115](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go#L115) | Mutates runtime log config. |

### 2.16 `marketplace` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `marketplace` | READ | Y | network | [cmd/mxcli/cmd_marketplace.go#L22](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L22) |  |
| `marketplace search` | READ | Y | network | [cmd/mxcli/cmd_marketplace.go#L35](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L35) |  |
| `marketplace info` | READ | Y | network | [cmd/mxcli/cmd_marketplace.go#L50](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L50) |  |
| `marketplace versions` | READ | Y | network | [cmd/mxcli/cmd_marketplace.go#L59](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L59) |  |
| `marketplace diff` | READ | Y | network | [cmd/mxcli/cmd_marketplace_diff.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_diff.go#L18) |  |
| `marketplace download` | WRITE | Y | network, files | [cmd/mxcli/cmd_marketplace.go#L69](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go#L69) | Writes `.mpk` to disk. |
| `marketplace install` | WRITE | Y | network, files | [cmd/mxcli/cmd_marketplace_install.go#L25](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_install.go#L25) | Rewrites `.mpr`. |
| `marketplace update` | WRITE | Y | network, files | [cmd/mxcli/cmd_marketplace_update.go#L17](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_update.go#L17) | Rewrites `.mpr`. |

### 2.17 `mcp` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `mcp` | READ | Y | network | [cmd/mxcli/mcp.go#L13-L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/mcp.go#L13-L18) | mxcli acts as MCP CLIENT to Studio Pro's embedded MCP server. NOT an MCP server (confirmed in inventory §5). |
| `mcp capabilities` | READ | Y | network | [cmd/mxcli/mcp.go#L20-L51](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/mcp.go#L20-L51) | Prints what the server can author. |

### 2.18 `playwright` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `playwright` | WRITE | Y | process, files | [cmd/mxcli/cmd_playwright.go#L19](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L19) | Parent. |
| `playwright status` | READ | Y | — | [cmd/mxcli/cmd_playwright.go#L143](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go#L143) |  |
| `playwright verify` | WRITE | Y | process, files | [cmd/mxcli/cmd_playwright.go#L25](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_playwright.go#L25) | Runs playwright-cli scripts against a running app; writes traces/screenshots. |
| `playwright open` | WRITE | Y | process | [cmd/mxcli/cmd_playwright.go#L112](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_playwright.go#L112) | Opens or attaches to a persistent browser session. |
| `playwright close` | WRITE | Y | process | [cmd/mxcli/cmd_playwright.go#L154](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_playwright.go#L154) | Closes the browser session. |
| `playwright check` | WRITE | Y | process, network | [cmd/mxcli/cmd_playwright.go#L166](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_playwright.go#L166) | Text verdict for pages of a running app; logs in when needed. |

### 2.19 `run` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `run` | WRITE | Y | process, files | [cmd/mxcli/cmd_run.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run.go#L18) | Boots the app locally; writes deployment artefacts, logs, lifecycle state. |
| `run status` | READ | Y | — | [cmd/mxcli/cmd_run_lifecycle.go#L60](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L60) |  |
| `run wait` | READ | Y | — | [cmd/mxcli/cmd_run_lifecycle.go#L100](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L100) |  |
| `run stop` | WRITE | Y | process | [cmd/mxcli/cmd_run_lifecycle.go#L79](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L79) |  |
| `run restart` | WRITE | Y | process | [cmd/mxcli/cmd_run_lifecycle.go#L137](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go#L137) |  |

### 2.20 `setup` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `setup` | WRITE | Y | network, files | [cmd/mxcli/setup.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/setup.go#L18) |  |
| `setup mxbuild` | WRITE | Y | network, files | [cmd/mxcli/setup.go#L37](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/setup.go#L37) | Downloads MxBuild from the Mendix CDN under ~/.mxcli/. |
| `setup mxruntime` | WRITE | Y | network, files | [cmd/mxcli/setup.go#L146](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/setup.go#L146) | Downloads the Mendix runtime from the Mendix CDN. |
| `setup mxcli` | WRITE | Y | network, files | [cmd/mxcli/setup.go#L282](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/setup.go#L282) | Downloads an mxcli binary from GitHub releases (default ./mxcli). |

### 2.21 `skill` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `skill` | READ | Y | — | [cmd/mxcli/cmd_skill.go#L40](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L40) |  |
| `skill list` | READ | Y | — | [cmd/mxcli/cmd_skill.go#L51](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L51) |  |
| `skill add` | WRITE | Y | files | [cmd/mxcli/cmd_skill.go#L97](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L97) | Writes skill files. |
| `skill remove` | WRITE | Y | files | [cmd/mxcli/cmd_skill.go#L243](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L243) |  |
| `skill upgrade` | WRITE | Y | files | [cmd/mxcli/cmd_skill.go#L263](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go#L263) |  |

### 2.22 `theme` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `theme` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L18](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L18) |  |
| `theme list` | READ | Y | — | [cmd/mxcli/cmd_theme.go#L59](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L59) |  |
| `theme show` | READ | Y | — | [cmd/mxcli/cmd_theme.go#L100](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L100) |  |
| `theme switcher` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L407](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L407) |  |
| `theme switcher install` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L425](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_theme.go#L425) |  |
| `theme create` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L167](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_theme.go#L167) | Scaffolds a project-local theme. |
| `theme apply` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L282](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_theme.go#L282) | Writes theme files into the project (styling only, no model change). |
| `theme remove` | WRITE | Y | files | [cmd/mxcli/cmd_theme.go#L362](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_theme.go#L362) | Removes a theme's generated blocks from project files. |

### 2.23 `widget` subtree

| Command | Class | Verified | Side effects | Source | Notes |
|---|---|---|---|---|---|
| `widget` | WRITE | Y | files | [cmd/mxcli/cmd_widget.go#L20](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L20) |  |
| `widget list` | READ | Y | — | [cmd/mxcli/cmd_widget.go#L42](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L42) |  |
| `widget docs` | WRITE | Y | files | [cmd/mxcli/cmd_widget.go#L69](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget.go#L69) | Reclassified READ→WRITE in phase 2.2: writes SKILL.md plus one file per widget into .ai-context/skills/widgets/ and .claude/skills/widgets/ (cmd_widget.go#L68-L76). |
| `widget describe` | READ | Y | — | [cmd/mxcli/cmd_widget_describe.go#L46](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_widget_describe.go#L46) |  |
| `widget extract` | WRITE | Y | files | [cmd/mxcli/cmd_widget.go#L25](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_widget.go#L25) | Writes a widget definition from an .mpk (default .mxcli/widgets/). |
| `widget init` | WRITE | Y | files | [cmd/mxcli/cmd_widget.go#L49](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_widget.go#L49) | Writes .def.json definitions for all project widgets. |
| `widget sync` | WRITE | Y | files | [cmd/mxcli/cmd_widget_sync.go#L29](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_widget_sync.go#L29) | Rewrites the .mpr to reconcile stored widget instances with installed packages. |

<!-- END GENERATED -->

### Not command paths

These rows are behaviours of a path above, not paths of their own, so they
have no row in `policy/mxcli-commands.json`:

- **Root with no subcommand** (REPL, or `-c "<MDL>"`): READ for the REPL
  itself; `-c` is classified by its MDL statements (ADR-0015).
  [cmd/mxcli/main.go#L106-L217](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/main.go#L106-L217).
- **`check --post-migration`**: a flag of `check`; legacy-widget scan, read-only.
  [cmd/mxcli/cmd_check.go#L482-L510](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check.go#L482-L510).

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
- **Linux `--help` tree on a workstation.** CI walks the pinned Linux binary
  (`mxcli command-tree check`). Locally on 2026-10-21 we walked the v0.26.0
  Windows asset instead (see §8.1); the two are built from the same tag, but
  only CI covers the Linux build.
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

### 8.1 Phase 2.2 reconciliation with the released binary (2026-10-21)

CI reported 34 paths in the binary but not in the inventory, and 3 paths in
the inventory but not in the binary (`diag session-report`,
`extract-templates`, `mcp capabilities`).

- **The 3 "missing" paths were a parser bug in our check, not hidden
  commands.** cobra pads command names to the longest name in the block
  (minimum 11) and then prints one space. `check_mxcli_tree.py` required two
  spaces after the name, so the longest name of 11+ characters in a block was
  dropped. In v0.26.0 that is `extract-templates` (root), `session-report`
  (`diag`), `capabilities` (`mcp`) and `design-properties` (`fix`). The last
  one was hidden from the report because it was in neither list. Source has
  no `Hidden: true` anywhere under `cmd/mxcli/`, and none of the
  `//go:build` files registers a command, so no row needs `hidden` or
  `build_condition`. All three register unconditionally:
  [mcp.go#L54-L55](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/mcp.go#L54-L55),
  [diag_session_report.go#L120](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/diag_session_report.go#L120),
  [cmd_extract_templates.go#L37](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_extract_templates.go#L37).
- **Evidence.** The v0.26.0 asset `mxcli-windows-amd64.exe` (SHA-256
  `3e88f3e09335a10eb53289681a8ec73930ce81ad2dd2b70cb836bfac89b637c6`;
  `mxcli version v0.26.0 (2026-10-11T18:37:07Z)`) reproduced CI's 34 + 3
  report exactly with the old parser. With the fixed parser it gives 35 + 0;
  after this reconciliation, 156 discovered paths match the inventory. Only
  `--help` and `--version` were run. The walk also hit a cp1252 decode error
  on Windows, so the checker now decodes help output as UTF-8.
- **35 rows added**, each with class, source line and side effects: the 34
  from CI plus `fix design-properties`. `completion` and its four shells are
  cobra's built-in command (READ, no side effects).
- **One reclassification:** `widget docs` READ → WRITE (`files`). Its `Long`
  says it writes `SKILL.md` and per-widget files into
  `.ai-context/skills/widgets/` and `.claude/skills/widgets/`
  ([cmd_widget.go#L68-L76](https://github.com/mendixlabs/mxcli/blob/12ce281622a1a78ebb6737e61fe6b5ea78c59e45/cmd/mxcli/cmd_widget.go#L68-L76)).
- The §2 tables are now generated from `policy/mxcli-commands.json`
  (ADR-0035); notes from the old hand-written tables moved into the JSON's
  `notes` fields.
