---
name: intake
description: Capture a Mendix change request from the user and record it as a task label. Use when the orchestrator starts a new task.
---

# Intake

1. Ask the user for the module, entity, and change.
2. Pick a short kebab-case task label (`add-customer-email`, `fix-order-index`).
3. Record it in `.mxagent/artefacts/<task>/intake.md`.
