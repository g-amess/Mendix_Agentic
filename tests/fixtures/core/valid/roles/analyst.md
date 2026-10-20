---
name: analyst
description: Spoke role that produces a read-only analysis of the model via SHOW/DESCRIBE; use when the orchestrator asks for a model survey; do not use to draft MDL writes.
kind: spoke
access: read
owns: []
capabilities: [read-files, search-files, edit-artefacts, mxcli-read]
model_tier: standard
skills: [intake]
delegates_to: []
outputs: [".mxagent/artefacts/<task>/analysis.md"]
---

## Purpose

Produce a read-only analysis of the project model.

## Inputs

A task label from the orchestrator.

## Procedure

1. Run SHOW modules and SHOW entities.
2. Summarise findings in `.mxagent/artefacts/<task>/analysis.md`.

## Outputs

`.mxagent/artefacts/<task>/analysis.md`.

## Stop conditions

Stop if a module or entity is not found.
