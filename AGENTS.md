# AGENTS.md — contributor instructions for this repo

These instructions are for **agents (and humans) contributing to _this_ repo**.
They are **not** shipped as project content to downstream Mendix apps.

Shipped content lives under `core/` (see ADR-0002).

## Purpose

Mendix_Agentic is an org-wide, agent-agnostic toolkit for building Mendix apps
with [mxcli](https://github.com/mendixlabs/mxcli) under hub-and-spoke orchestration.
Phase 1 scope is **foundation and safety only**: skeleton, decisions, version
matrix, doctor, and the mxcli policy guard. No agents, skills, slash commands,
plugins or marketplace files.

## Repo map

```
.
├── README.md                    user-facing
├── AGENTS.md                    this file (contributor rules)
├── CLAUDE.md                    thin pointer to AGENTS.md
├── adapters/                    tool-specific generators (empty, phase 2+)
├── bin/
│   └── doctor[.py|.cmd]         prerequisite checker, stdlib only
├── bootstrap/                   first-run setup helpers (empty, phase 2+)
├── core/
│   ├── roles/                   canonical role descriptions (empty)
│   └── skills/                  canonical skill definitions (empty)
├── docs/
│   ├── decisions/               ADRs (0000-template + 0001–0008)
│   ├── research/                fact-check notes (mxcli-inventory.md)
│   ├── version-matrix.md
│   └── mxcli-bugs.md
├── plugins/                     tool-specific plugin bundles (empty, phase 3+)
├── policy/
│   ├── mxcli_guard.py           PreToolUse hook + CLI check
│   ├── mxcli-commands.json      command → READ|WRITE classification
│   ├── ownership.json           agent → allowed write classes
│   └── stop-operations.json     always-denied MDL statements
└── tests/
    ├── fixtures/hooks/          PreToolUse JSON payloads
    └── policy/                  unittest for the guard
```

## Non-negotiables

1. **Canonical content is plain markdown under `core/`.** Tool-specific files
   (`.claude/`, `.cursor/`, `AGENTS.md` project blocks, etc.) are *generated* by
   `adapters/`. Do not hand-maintain duplicates. (ADR-0001)
2. **Hub and spoke.** The orchestrator is the only hub. Spokes never call other
   spokes; hand-offs go via the orchestrator and must leave a written artefact
   (a note, a draft, a check result). (ADR-0003)
3. **Read before write.** Any agent touching a Mendix model runs `SHOW` /
   `DESCRIBE` first. No `.mpr` write without the sequence
   `draft → mxcli check → human approval → mxcli exec`. (ADR-0004)
4. **Least privilege.** Only the designated writer agent (phase 3+) runs
   `mxcli exec`. Analysts, reviewers and planners run read-only commands only.
   Enforced by `policy/ownership.json`.
5. **Judgement in skills, facts in scripts.** Decisions that depend on taste or
   context go into skills (prose, examples). Deterministic facts (command
   classifications, version numbers, lock-file paths) go into JSON/scripts the
   guard can enforce.
6. **No client or project specifics in this repo.** No customer names, no
   project paths, no personal filesystem paths, no credentials. Examples are
   generic (`example.mpr`, `~/projects/<app>`).
7. **Every rule or command states the Mendix and mxcli versions it applies to.**
   If a note holds only for mxcli ≥ v0.26.0 and Studio Pro 11.12 LTS, say so.
   See `docs/version-matrix.md`.

## Verifying mxcli facts

mxcli is upstream, moves, and we have been bitten before. For any mxcli claim
you add to this repo:

- Cite a permalink into [`mendixlabs/mxcli`](https://github.com/mendixlabs/mxcli)
  at a specific commit, or a release note, or a page on
  [mxcli.org](https://mxcli.org).
- If you cannot confirm, mark the item **UNVERIFIED** inline and record what
  you tried. The guard treats UNVERIFIED commands as WRITE (ADR-0007).
- Never guess at `init` behaviour, hook shapes, or lock-file names. If you did
  not read the source, say so.

## Language and spelling

South African English. `authorise`, `organisation`, `behaviour`, `colour`,
`defence`. US spellings only where they appear in third-party code or data.

## Recording a decision

1. Copy `docs/decisions/0000-template.md` to `docs/decisions/NNNN-short-slug.md`
   where `NNNN` is the next free ID.
2. Fill in Context / Decision / Consequences / Versions.
3. Set status to `Proposed`. Open a PR.
4. On merge, bump status to `Accepted` and add a row to
   `docs/decisions/README.md`.
5. Superseded ADRs stay in the tree; mark `Status: Superseded by ADR-NNNN`.

## When something upstream breaks

Log it in `docs/mxcli-bugs.md` with mxcli version, Mendix version, symptom,
workaround and a "Retested on vX.Y.Z" line. Add a row to the version matrix if
the minimum shifts.

## Threat model

See [`docs/threat-model.md`](docs/threat-model.md) for what the guard
protects against (agent mistakes, drift, accidental writes to open models)
and what it does not (a deliberately obfuscating agent). The backstops —
git snapshots, mxcli's lock check, human approval, CI — are listed there.

## Phase 1 scope reminder

If you find yourself writing a skill, agent definition, slash command, plugin
manifest, marketplace entry, or adding hooks/permissions to this repo's own
`.claude/settings.json` — stop. That is phase 2+.
