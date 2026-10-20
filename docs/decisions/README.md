# Architecture Decision Records

Each ADR is a numbered, immutable record of a decision. Context first, then the
decision and its consequences. Superseded records stay in the tree with a
`Superseded by ADR-NNNN` note at the top.

Use `0000-template.md` as the starting point.

## Index

| ID   | Date       | Title                                                                   | Status   |
| ---- | ---------- | ----------------------------------------------------------------------- | -------- |
| 0001 | 2026-10-20 | Canonical instructions live in plain markdown under `core/`             | Accepted |
| 0002 | 2026-10-20 | Root `AGENTS.md` is for contributors to this repo                       | Accepted |
| 0003 | 2026-10-20 | Hub and spoke; orchestrator is the main thread                          | Accepted |
| 0004 | 2026-10-20 | One writer to the `.mpr` at a time                                      | Accepted |
| 0005 | 2026-10-20 | Guardrails enforced by tool-agnostic policy scripts                     | Accepted |
| 0006 | 2026-10-20 | Policy and setup scripts are Python 3 stdlib only                       | Accepted |
| 0007 | 2026-10-20 | Unknown or unverified mxcli commands are treated as writes              | Accepted |
| 0008 | 2026-10-20 | Mendix depth lives in skills and lint rules, not agent bios             | Accepted |
| 0009 | 2026-10-20 | Work happens on a branch per phase, merged via PR                       | Accepted |
| 0010 | 2026-10-20 | The policy guard fails closed                                           | Accepted |
| 0011 | 2026-10-20 | mxcli safety overrides are denied by the guard                          | Accepted |
| 0012 | 2026-10-20 | mxcli command classifications come from source or `--help`              | Accepted |
| 0013 | 2026-10-20 | mxcli is pinned at v0.26.0                                              | Accepted |
| 0014 | 2026-10-20 | Unlisted mxcli command paths are WRITE; children never inherit READ    | Accepted |
| 0015 | 2026-10-20 | Root mxcli invocations are classified by their MDL statements          | Accepted |
| 0016 | 2026-10-20 | Bash is the supported agent shell; PowerShell is a backstop            | Accepted |
| 0017 | 2026-10-20 | The guard protects against agent mistakes, not deliberate evasion      | Accepted |
| 0018 | 2026-10-20 | Role cards declare abstract capabilities and model tiers               | Accepted |
| 0019 | 2026-10-20 | `policy/ownership.json` is generated from role cards                   | Accepted |
| 0020 | 2026-10-20 | Generated adapter output is committed as copies; CI fails on drift     | Accepted |
| 0021 | 2026-10-20 | Canonical frontmatter is a restricted YAML subset                      | Accepted |
| 0022 | 2026-10-20 | The Claude Code plugin is `mendix-agentic`; this repo is its marketplace | Accepted |
| 0023 | 2026-10-20 | Only the Claude Code adapter is built now                              | Accepted |
| 0024 | 2026-10-20 | CI checks the installed mxcli's command tree against the inventory     | Accepted |
