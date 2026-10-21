---
name: hub
description: Fixture hub role that delegates to spoke-a and spoke-b; use to test tool-list emission.
kind: hub
access: read
owns: []
capabilities: [read-files, search-files, delegate]
model_tier: standard
skills: []
delegates_to: [spoke-b, spoke-a]
outputs: [".mxagent/artefacts/<task>/hub.md"]
---

## Purpose

Fixture hub.

## Inputs

A user request.

## Procedure

1. Delegate to spoke-a and spoke-b.

## Outputs

`.mxagent/artefacts/<task>/hub.md`.

## Stop conditions

Stop when both spokes report.
