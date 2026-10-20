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
