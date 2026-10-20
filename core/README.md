# core/ — canonical, tool-agnostic content

This directory holds the *source of truth* for Mendix_Agentic. Adapters under
[`adapters/`](../adapters) project this into tool-specific layouts (phase 2:
Claude Code). Nothing agent-shaped lives at this layer — just plain markdown
and JSON that any adapter can consume.

## Layout

```
core/
├── README.md              you are here
├── capabilities.json      the capability registry (see §2)
├── roles/<name>.md        canonical role cards (see §1)
└── skills/<name>/SKILL.md canonical skills (see §3)
```

## 1. Role card (`core/roles/<name>.md`)

A role card is markdown with YAML-ish frontmatter and five required body
sections. The frontmatter is parsed by `adapters/lib/frontmatter.py` (a
restricted subset — ADR-0021).

### Frontmatter — required fields

| Field | Type | Meaning |
|---|---|---|
| `name` | string | kebab-case, unique, must match the filename (without `.md`). |
| `description` | string | One or two sentences used for routing. **Must say when to use AND when not to.** ≤ 400 characters. |
| `kind` | string | `hub` or `spoke`. |
| `access` | string | `read` or `write`. |
| `owns` | list of string | Write classes this role may perform. Empty for `access: read`. Classes defined in [`policy/write-classes.json`](../policy/write-classes.json). |
| `capabilities` | list of string | Entries from [`core/capabilities.json`](capabilities.json). |
| `model_tier` | string | `fast`, `standard`, or `deep`. Adapters map this to a model alias (e.g. `fast → haiku`). |
| `skills` | list of string | Skill names to preload. Each must exist under `core/skills/<name>/`. |
| `delegates_to` | list of string | Role names this role may delegate to. **Only valid on `kind: hub`**; spokes must have `[]`. |
| `outputs` | list of string | Artefact path patterns this role writes, e.g. `.mxagent/artefacts/<task>/analysis.md`. |

### Frontmatter — restrictions

- No other keys. The validator rejects unknown fields with a file:line error.
- `access: read` → `owns` must be `[]`, and `capabilities` must not contain
  `mxcli-write`. (`edit-artefacts` is **allowed** for read roles — read roles
  still produce reports under `.mxagent/artefacts/`.)
- `access: write` → `owns` must be non-empty and reference defined classes.
- At most one role owns a given write class (ADR-0004).
- `kind: spoke` → `delegates_to` must be `[]` and `capabilities` must not
  include `ask-human`.

### Required body sections

Exactly these five, as `## Purpose`, `## Inputs`, `## Procedure`,
`## Outputs`, `## Stop conditions`. The validator fails if any are missing.

## 2. Capability registry (`core/capabilities.json`)

Every entry in a role's `capabilities` list must come from this registry.
Each capability has an `id`, a `description`, and a `read_only` boolean.
`ask-human` is a special capability — it is only valid on `kind: hub`
(subagents cannot interrupt the user).

## 3. Skill (`core/skills/<name>/SKILL.md`)

Skills follow the Agent Skills specification at
[agentskills.io/specification](https://agentskills.io/specification).

### Allowed frontmatter fields (per spec)

| Field | Required | Notes |
|---|---|---|
| `name` | yes | 1–64 chars, lowercase alnum + hyphens, matches the parent folder name. |
| `description` | yes | 1–1024 chars; what the skill does *and* when to use it. |
| `license` | no | SPDX name or a reference to a bundled licence file. |
| `compatibility` | no | ≤ 500 chars. Environment requirements. |
| `metadata` | no | Map of string → string. |
| `allowed-tools` | no | Space-separated string. Experimental; support varies. |

The validator rejects any other key in the SKILL.md frontmatter.

### Tool-specific extras — JSON sidecar

For Claude Code-specific fields (`disable-model-invocation`, `user-invocable`,
`allowed-tools` extensions, `context`, `agent`, `paths`), create
`core/skills/<name>/adapter.claude.json` next to the SKILL.md. The Claude
adapter merges these into the frontmatter at build time (ADR-0021). Other
adapters ignore the sidecar.

### Optional directories

A skill may bundle `scripts/`, `references/`, and `assets/` directories.
These are copied verbatim by the Claude adapter.

## How roles become Claude Code agents

The Claude adapter (`adapters/claude/build.py`):

1. Reads every role card in `core/roles/`.
2. Maps each `capabilities` entry to Claude Code tool names via
   `adapters/claude/capability-map.json` (e.g. `search-files → Grep, Glob`,
   `mxcli-read → Bash`, `delegate → Agent(<delegates_to...>)`).
3. Maps `model_tier` to a Claude model alias (`fast → haiku`, `standard →
   sonnet`, `deep → opus`).
4. Writes `plugins/mendix-agentic/agents/<name>.md` with the required
   subagent frontmatter from
   [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents).
5. Generates `plugins/mendix-agentic/policy/ownership.json` from the `owns`
   fields of all write roles (ADR-0019). The file is marked GENERATED — do
   not edit.

Plugin subagents **ignore** `hooks`, `mcpServers`, and `permissionMode`
(per the Claude Code plugin docs), so the adapter does not emit them.

## When to add a new field to a role card

Add a field to the restricted frontmatter only when every supported adapter
can map it to something concrete. Tool-specific extras go in JSON sidecars
alongside the role card (`<name>.claude.json`), not in the main file.
