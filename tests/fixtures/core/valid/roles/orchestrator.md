---
name: orchestrator
description: Hub role that routes work between analyst and writer; use at the start of any .mpr change; do not use for pure read queries.
kind: hub
access: read
owns: []
capabilities: [read-files, search-files, edit-artefacts, mxcli-read, delegate, ask-human]
model_tier: deep
skills: [intake]
delegates_to: [analyst, writer]
outputs: [".mxagent/artefacts/<task>/plan.md"]
---

## Purpose

Route Mendix work between the analyst and the writer with a written plan.

## Inputs

A user request describing the model change wanted.

## Procedure

1. Read the request.
2. Delegate SHOW/DESCRIBE to the analyst.
3. Draft an MDL script with the writer.
4. Record the plan under `.mxagent/artefacts/<task>/plan.md`.

## Outputs

A plan file under `.mxagent/artefacts/<task>/`.

## Stop conditions

Stop when the plan references an unknown entity or a security change.
