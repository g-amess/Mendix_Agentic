---
name: spoke-b
description: Fixture spoke role spoke-b; read-only; use when the hub delegates a survey.
kind: spoke
access: read
owns: []
capabilities: [read-files]
model_tier: fast
skills: []
delegates_to: []
outputs: [".mxagent/artefacts/<task>/spoke-b.md"]
---

## Purpose

Fixture spoke.

## Inputs

A task label from the hub.

## Procedure

1. Read files.

## Outputs

`.mxagent/artefacts/<task>/spoke-b.md`.

## Stop conditions

Stop when done.
