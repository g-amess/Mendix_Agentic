---
name: mdl-draft
description: Draft an MDL script that effects the requested model change. Use when the writer needs an input script before running `mxcli check`.
license: Apache-2.0
compatibility: Requires mxcli v0.26.0 or later
metadata:
  tier: core
---

# Draft an MDL script

1. Read the analyst report under `.mxagent/artefacts/<task>/analysis.md`.
2. Write a CREATE / ALTER / RENAME sequence as plain MDL.
3. End every statement with `;`.
