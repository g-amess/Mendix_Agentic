# mxcli inventory (v0.26.0)

Last reviewed: 2026-10-20. Source of record: `mendixlabs/mxcli` at tag
[`v0.26.0`](https://github.com/mendixlabs/mxcli/tree/v0.26.0) (released
2026-10-11, per the Releases page). Where a specific file/line could not be
confirmed, the row is marked **UNVERIFIED** with the trail of what was
checked. Anything UNVERIFIED is treated as **WRITE** by the policy guard
(ADR-0007).

## Version used

- Tag: [`v0.26.0`](https://github.com/mendixlabs/mxcli/tree/v0.26.0)
- Nearest newer tag at time of check: v0.27.0 (2026-10-15).

## Top-level commands

The command surface was derived from the files in
[`cmd/mxcli/`](https://github.com/mendixlabs/mxcli/tree/v0.26.0/cmd/mxcli)
(file-per-command convention: `cmd_<name>.go`) cross-checked against the
public README. Several READMEs mention commands that do not appear as
dedicated `cmd_*.go` files (e.g. `list`, `search`, `callers`, `impact`,
`docker`, `test`, `tunnel-hub`, `setup`, `syntax`) — these are **UNVERIFIED
as to implementation path**: they may be aliases, subcommands of other
roots (e.g. `catalog`, `brain`), or registered dynamically. They are still
listed below with the best-available classification. Agents must treat
UNVERIFIED rows as WRITE.

| Command             | Class  | Verified     | Source                                                                                                                                    | Notes                                                                                                 |
| ------------------- | ------ | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `show`              | READ   | Y            | [cmd_show.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_show.go) (`Short: "List project elements"`)                   | Also exposed as `list` (alias). Reads project, writes to stdout only.                                 |
| `list`              | READ   | Y            | Alias of `show`.                                                                                                                          |                                                                                                       |
| `describe`          | READ   | UNVERIFIED   | [cmd_describe.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_describe.go)                                             | README calls it "View element details". Classified READ pending file read.                            |
| `search`            | READ   | UNVERIFIED   | README mentions as top-level; no dedicated `cmd_search.go` seen.                                                                          | Likely implemented under another root. Treat as WRITE until confirmed.                                |
| `callers`           | READ   | UNVERIFIED   | README mentions as top-level; no dedicated `cmd_callers.go` seen.                                                                         | Likely a `query` subcommand (`cmd_query.go` exists).                                                  |
| `callees`           | READ   | UNVERIFIED   | README mentions as top-level; no dedicated `cmd_callees.go` seen.                                                                         |                                                                                                       |
| `refs`              | READ   | UNVERIFIED   | README mentions as top-level; no dedicated file seen.                                                                                     |                                                                                                       |
| `impact`            | READ   | UNVERIFIED   | README mentions as top-level; no dedicated file seen.                                                                                     |                                                                                                       |
| `context`           | READ   | UNVERIFIED   | README mentions as top-level; no dedicated file seen.                                                                                     |                                                                                                       |
| `catalog`           | UNKNOWN| UNVERIFIED   | [cmd_catalog.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_catalog.go)                                               | Not inspected. Default WRITE.                                                                         |
| `changelog`         | READ   | UNVERIFIED   | [cmd_changelog.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_changelog.go)                                           | Likely read-only report. Treat as WRITE until confirmed.                                              |
| `check`             | READ   | Y            | [cmd_check.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check.go) (`Short: "Check an MDL script for errors without executing it"`) | Writes a *temporary* scratch copy via `scriptdiff.NewScratch` + `scratch.Apply` (deferred Close). The project itself is not changed; classify READ with watch-out note. |
| `check post-migration` | READ | UNVERIFIED | [cmd_check_post_migration.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_check_post_migration.go)                     | Not inspected.                                                                                        |
| `constant`          | UNKNOWN| UNVERIFIED   | [cmd_constant.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_constant.go)                                             |                                                                                                       |
| `debug`             | UNKNOWN| UNVERIFIED   | [cmd_debug.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_debug.go)                                                   |                                                                                                       |
| `diff`              | READ   | UNVERIFIED   | [cmd_diff.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_diff.go)                                                     | README: "Preview changes". Treat as WRITE until confirmed.                                            |
| `eval`              | UNKNOWN| UNVERIFIED   | [cmd_eval.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval.go)                                                     |                                                                                                       |
| `eval run`          | UNKNOWN| UNVERIFIED   | [cmd_eval_run.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_eval_run.go)                                             |                                                                                                       |
| `exec`              | WRITE  | Y            | [cmd_exec.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go)                                                     | Executes MDL against the `.mpr`. Lock-file check present (see below). `--no-check` skips validation. `--force` bypasses Studio Pro lock. |
| `extract templates` | WRITE  | UNVERIFIED   | [cmd_extract_templates.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_extract_templates.go)                           | Name implies file writes.                                                                             |
| `fix`               | WRITE  | UNVERIFIED   | [cmd_fix.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix.go)                                                       | `fix` strongly implies mutation.                                                                      |
| `fix hashes`        | WRITE  | UNVERIFIED   | [cmd_fix_hashes.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix_hashes.go)                                         |                                                                                                       |
| `fix property-sets` | WRITE  | UNVERIFIED   | [cmd_fix_property_sets.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fix_property_sets.go)                           |                                                                                                       |
| `fmt`               | WRITE  | UNVERIFIED   | [cmd_fmt.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_fmt.go)                                                       | Formatters typically rewrite files in place.                                                          |
| `git`               | UNKNOWN| UNVERIFIED   | [cmd_git.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_git.go)                                                       | Includes `mxcli git note` per release notes.                                                          |
| `graph report`      | READ   | UNVERIFIED   | [cmd_graph_report.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_graph_report.go)                                     | Likely emits a report file (would still be WRITE).                                                    |
| `help code`         | READ   | UNVERIFIED   | [cmd_help_code.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_help_code.go)                                           |                                                                                                       |
| `layout`            | UNKNOWN| UNVERIFIED   | [cmd_layout.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout.go)                                                 |                                                                                                       |
| `layout flows`      | UNKNOWN| UNVERIFIED   | [cmd_layout_flows.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_layout_flows.go)                                     |                                                                                                       |
| `lint`              | READ   | UNVERIFIED   | [cmd_lint.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_lint.go)                                                     | README: "Check projects for common issues." Treat as WRITE until confirmed.                           |
| `log`               | READ   | UNVERIFIED   | [cmd_log.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_log.go)                                                       |                                                                                                       |
| `marketplace`       | UNKNOWN| UNVERIFIED   | [cmd_marketplace.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace.go)                                       |                                                                                                       |
| `marketplace diff`  | READ   | UNVERIFIED   | [cmd_marketplace_diff.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_diff.go)                             |                                                                                                       |
| `marketplace install` | WRITE | UNVERIFIED | [cmd_marketplace_install.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_install.go)                        |                                                                                                       |
| `marketplace update`  | WRITE | UNVERIFIED | [cmd_marketplace_update.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_marketplace_update.go)                          |                                                                                                       |
| `new`               | WRITE  | UNVERIFIED   | [cmd_new.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_new.go)                                                       | Creates a new project (scaffold).                                                                     |
| `new java`          | WRITE  | UNVERIFIED   | [cmd_new_java.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_new_java.go)                                             |                                                                                                       |
| `new layout`        | WRITE  | UNVERIFIED   | [cmd_new_layout.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_new_layout.go)                                         |                                                                                                       |
| `add-tool`          | WRITE  | Y            | [cmd_add_tool.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_add_tool.go) (writes `toolConfig.Files` via `os.WriteFile`) | Writes tool-specific config into the target project. Claude Code target writes `.claude/settings.json`, `CLAUDE.md`, commands, lint-rules, `lint-config.yaml`, skills — but the `SupportedTools` map (hooks? permissions?) is in a separate file and is **UNVERIFIED**. |
| `init`              | WRITE  | UNVERIFIED   | README advertises `mxcli init`. No `cmd_init.go` found in cmd/mxcli root. Possibly a wrapper around `add-tool`, or registered under another file. | Treat as WRITE. Needs confirmation of file list and whether it configures hooks/permissions in `.claude/settings.json`. |
| `playwright`        | UNKNOWN| UNVERIFIED   | [cmd_playwright.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_playwright.go)                                         | Browser automation; may write artefacts (screenshots, videos).                                        |
| `query`             | READ   | UNVERIFIED   | [cmd_query.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_query.go)                                                   | Likely the backend for `search`/`callers`/`callees`/`refs`.                                           |
| `rename`            | WRITE  | UNVERIFIED   | [cmd_rename.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_rename.go)                                                 | Clearly mutating.                                                                                     |
| `report`            | WRITE  | UNVERIFIED   | [cmd_report.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_report.go)                                                 | Likely emits report files to disk.                                                                    |
| `run`               | WRITE  | UNVERIFIED   | [cmd_run.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run.go)                                                       | Runs app locally; produces logs, caches.                                                              |
| `run lifecycle`     | WRITE  | UNVERIFIED   | [cmd_run_lifecycle.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_run_lifecycle.go)                                   |                                                                                                       |
| `skill`             | UNKNOWN| UNVERIFIED   | [cmd_skill.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_skill.go)                                                   |                                                                                                       |
| `auth` / `auth hub` | UNKNOWN| UNVERIFIED   | [cmd_auth.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth.go), [cmd_auth_hub.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_auth_hub.go) | Credential cache WRITE on login.                                                                      |
| `brain`             | UNKNOWN| UNVERIFIED   | [cmd_brain.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_brain.go)                                                   |                                                                                                       |
| `bson` / `bson discover` / `bson dump` | UNKNOWN | UNVERIFIED | [cmd_bson.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_bson.go), …                                                   |                                                                                                       |
| `docker`            | WRITE  | UNVERIFIED   | README mentions as top-level ("Run and test Mendix applications"); no `cmd_docker.go` in cmd/mxcli root; a `docker/` subdirectory exists. | README calls out `docker` as "watch-out" (looks like container tooling but may build/cache).          |
| `test`              | WRITE  | UNVERIFIED   | README mentions as top-level ("Run microflow tests"); no `cmd_test.go` found; `testrunner/` subdirectory present.                           | Writes test logs, caches.                                                                             |
| `tunnel-hub`        | WRITE  | UNVERIFIED   | README mentions; `tunnelhub/` subdirectory present.                                                                                       | Starts a service; writes PID/log files.                                                               |
| `setup`             | WRITE  | UNVERIFIED   | README mentions ("Configure MxBuild and dependencies"); no dedicated `cmd_setup.go` found.                                                 | Installs tooling into user profile.                                                                   |
| `syntax`            | READ   | UNVERIFIED   | README mentions ("Display language reference"); `syntax/` subdirectory present.                                                           |                                                                                                       |

### Watch-out: "looks read-only but writes" cases

- **`mxcli check`** writes a *temporary* scratch copy of the project
  (`scriptdiff.NewScratch` + `scratch.Apply`, closed via `defer`). The
  original `.mpr` is not changed, but the command does hit disk. Keep this
  in mind if you are policing filesystem writes rather than `.mpr` writes.
- **`mxcli docker`** is a top-level command grouped with other analysis
  tools but likely builds images, pulls layers, and writes to the Docker
  cache. The README explicitly lists it under "Run and test Mendix
  applications." Treat as WRITE.
- **`mxcli test`** reads from the project but writes test logs, reports and
  (depending on invocation) a running runtime. Treat as WRITE.
- **`mxcli fmt`**, **`mxcli fix*`**, **`mxcli rename`**, **`mxcli exec`**,
  **`mxcli new*`**, **`mxcli add-tool`**, **`mxcli init`**: unambiguously
  WRITE.

## `mxcli init` for the Claude Code target

**UNVERIFIED (partial).** From the public README, the Claude Code target
causes the following to be created in the project:

- `.claude/settings.json`
- `CLAUDE.md`
- `commands/` (slash-command directory)
- `lint-rules/`
- `lint-config.yaml` with the System module excluded from lint
- `skills/`
- `.devcontainer/` (per README passage: "`mxcli init` generates a
  `.devcontainer/` configuration that provides a sandboxed development
  environment")

The following remain **UNVERIFIED**:

- Whether `.claude/settings.json` includes `hooks` entries (e.g.
  `PreToolUse`, `PostToolUse`) by default, and the exact JSON shape used.
  The `cmd_add_tool.go` dispatcher writes files from a `SupportedTools` map
  held in a separate file that could not be located under
  `cmd/mxcli/skillpack/`. Attempted to fetch `cmd_init.go` directly and
  received 404 — no such file in `cmd/mxcli/` at v0.26.0.
- Whether `.claude/settings.json` includes a `permissions.allow` /
  `permissions.deny` block, and the entries.
- The exact marker strings written into `AGENTS.md` and `CLAUDE.md`
  (begin/end delimiters). The README confirms both files are touched; the
  delimiters are not quoted anywhere publicly visible.
- Whether `init` is a separate subcommand or a wrapper around `add-tool`.
  Both appear in the README under distinct bullets.

**Follow-up:** once a maintainer can run `mxcli init --help` or inspect the
source file that houses the Claude Code target definition, update this
section and promote the inventory rows to `Verified: Y`.

## MCP server mode

**UNVERIFIED (likely not present).** The README does not mention mxcli
exposing an MCP server. It describes an `--mcp` client backend flag that
routes operations through an MCP backend (i.e. mxcli *as a client*), and
there is a `mcpprobe` utility under `cmd/`. There is no `cmd_mcp.go` in
`cmd/mxcli/` at v0.26.0, no README reference to `mxcli mcp` as a
subcommand, no `serve` / `stdio` phrasing. If a server mode exists, it is
not advertised. Treat the capability as absent until confirmed.

## Studio Pro lock file

**Verified.** `cmd_exec.go` consults `mmpr.StudioProLockFile()` before
executing writes against the `.mpr`. The lock file is **`<project>.mpr.lock`,
located beside the `.mpr`**. If the lock is present and `--force` is not
set, exec is refused with an error. The environment variable
`MXCLI_ALLOW_STUDIO_PRO_OPEN=1` globally disables the check.

- Source: [cmd_exec.go](https://github.com/mendixlabs/mxcli/blob/v0.26.0/cmd/mxcli/cmd_exec.go)
  — "A write is refused while Studio Pro has the project open (its
  `<project>.mpr.lock` is beside the `.mpr`): Studio Pro does not reload
  the model from disk, and its next save would silently discard the
  change."

The policy guard uses this same filename (`<project>.mpr.lock`) in rule 6.

## Open UNVERIFIED items

- **Command classifications**: every row in the table marked `UNVERIFIED`
  needs the corresponding `cmd_*.go` file read (or `--help` captured on a
  real install) to confirm READ/WRITE and promote to `Verified: Y`.
- **`mxcli init` vs `mxcli add-tool`**: are they distinct, or is one an
  alias for the other? Needs `--help` capture.
- **`.claude/settings.json` shape** written by the Claude Code target:
  hooks? permissions?
- **AGENTS.md / CLAUDE.md marker blocks**: exact delimiter strings used.
- **MCP server mode**: definitively absent (not just undocumented)?
- **Commands not implemented under `cmd/mxcli/cmd_<name>.go`**: `list`
  (confirmed alias of `show`), `search`, `callers`, `callees`, `refs`,
  `impact`, `context`, `docker`, `test`, `tunnel-hub`, `setup`, `syntax`
  — where are these registered?
- **Studio Pro minimum version**: the lock-file check is in v0.26.0, but
  we have not pinned the oldest Studio Pro version it works against.
- **Verification method**: all of the above were read via `WebFetch`
  against GitHub's HTML; no local clone or installed binary was
  consulted. A direct source-tree walk at the tag would catch any
  summarisation errors.

## Verification trail

All checks performed 2026-10-20 via `WebFetch` against:

- `https://github.com/mendixlabs/mxcli` (README)
- `https://github.com/mendixlabs/mxcli/releases`
- `https://github.com/mendixlabs/mxcli/tree/v0.26.0`
- `https://github.com/mendixlabs/mxcli/tree/v0.26.0/cmd/mxcli`
- `https://raw.githubusercontent.com/mendixlabs/mxcli/v0.26.0/cmd/mxcli/cmd_show.go`
- `https://raw.githubusercontent.com/mendixlabs/mxcli/v0.26.0/cmd/mxcli/cmd_check.go`
- `https://raw.githubusercontent.com/mendixlabs/mxcli/v0.26.0/cmd/mxcli/cmd_exec.go`
- `https://raw.githubusercontent.com/mendixlabs/mxcli/v0.26.0/cmd/mxcli/cmd_add_tool.go`

Attempts that returned 404 (and therefore classified "not present at this
path"):

- `https://raw.githubusercontent.com/mendixlabs/mxcli/v0.26.0/cmd/mxcli/cmd_init.go`
