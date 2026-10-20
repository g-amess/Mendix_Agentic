# ADR-0017: The guard protects against agent mistakes, not deliberate evasion

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

We have a choice about how to describe `policy/mxcli_guard.py`: a safety
belt (friendly, caught the common failure, must not pretend to be a vault)
or a security control (adversarial threat model, must survive a hostile
agent). Those have very different design costs. If the guard is marketed
as adversarial-proof, every PowerShell workaround, every pipe-into-mxcli,
every environment-variable obfuscation becomes a bug.

## Decision

The guard protects against **agent mistakes**: the common failure of an
agent typing the wrong command, writing to a model while Studio Pro has it
open, or picking up a surprising new subcommand after an upgrade. It is
**not** a security control for a deliberately evasive agent.

The backstops that catch what the guard misses are:

1. **Git snapshots** — every WRITE runs against a committed model
   (R7a + R7), so recovery is `git restore`.
2. **mxcli's own Studio Pro lock check** — defence in depth with R6.
3. **Human approval gates** — the designated writer runs only when
   ownership is explicit (phase 1 ships `ownership.json` empty, so every
   WRITE is denied until a human adds a writer).
4. **CI** — doctor and the unittest suite run on every push and PR; the
   inventory-consistency test catches drift in `policy/mxcli-commands.json`.

This decision is documented in [docs/threat-model.md](../threat-model.md),
which is linked from `AGENTS.md`.

## Consequences

- Positive: Honest scope. We can refuse to chase every creative obfuscation
  as a guard bug; the right fix is often a backstop.
- Positive: Reviewers of future guard changes have a scope test ("would
  this stop a mistake?") rather than an impossible one ("would this stop
  an adversary?").
- Negative: Someone who assumes the guard is adversarial-proof may be
  surprised. We mitigate with the threat-model doc.
- Follow-ups: If adversarial behaviour becomes a real concern, phase 2+
  would move key enforcement out of the agent sandbox (git hooks, CI
  policy, server-side permission).

## Versions

- Applies to the guard regardless of version.

## References

- ADR-0004, ADR-0009, ADR-0010, ADR-0011, ADR-0016.
- `docs/threat-model.md`.
