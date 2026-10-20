# ADR-0010: The policy guard fails closed

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The guard sits between agents and `mxcli exec`. If a precondition cannot be
verified — git missing, cwd not in a repo, policy JSON unreadable, an
unhandled exception somewhere in the guard — the safe answer is **deny**.
"Allow unless we can prove this is bad" lets a buggy guard become no guard
at all.

## Decision

For any WRITE classification, the guard **denies** when:

- git is not on PATH, or
- the current working directory is not inside a git worktree, or
- the policy JSON files (`mxcli-commands.json`, `ownership.json`,
  `stop-operations.json`) cannot be loaded, or
- any code path in the guard raises an unhandled exception.

Each deny message states the specific precondition that failed and the
remediation. The guard also protects its own state: no agent-driven write to
`.mxagent/**` or `policy/**` is permitted (see rules R2a, R2b in
`policy/mxcli_guard.py`).

## Consequences

- Positive: Partial failures (torn JSON, interrupted git, dead symlink)
  degrade to deny, never to allow.
- Positive: Agents cannot rewrite the guard's own data from inside a tool call.
- Negative: Working from a non-git directory now requires `git init`.
  Acceptable — mxcli work is always inside a Mendix project repo.
- Follow-ups: Add structured error metrics to `.mxagent/guard.log` so the
  team can see fail-closed denies over time.

## Versions

- mxcli: any
- Python: 3.10+
- git: any

## References

- ADR-0005, ADR-0009.
