# ADR-0015: Root mxcli invocations are classified by their MDL statements

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

mxcli has two root-level invocation shapes that bypass the subcommand tree:

- `mxcli -p app.mpr -c "<mdl>"` — run an inline MDL script against a
  project. Useful for one-liners like `-c "SHOW modules"`.
- Bare `mxcli` (REPL) or `mxcli < script.mdl` (piped stdin) — interactive
  or stdin-fed MDL execution.

Both can read *or* write. "Treat `-c` as `exec`" is too strict (it blocks
every one-liner, including SHOWs). "Treat `-c` as READ" is unsafe (an
agent can inline a CREATE ENTITY).

## Decision

- **Rule R4-c**: for an mxcli invocation with no subcommand and `-c
  "<mdl>"`:
  1. Split the inline text on `;`.
  2. Strip `//` line comments and `/* … */` block comments.
  3. Classify as READ **only** if every non-empty statement begins with a
     verb in the confirmed read-verb set (SHOW, DESCRIBE, SELECT, OQL),
     taken from the MDL grammar's `dqlStatement` rule at the pinned
     SHA ([MDLParser.g4#L931-L936](https://github.com/mendixlabs/mxcli/blob/v0.26.0/mdl/grammar/MDLParser.g4#L931-L936)).
     EXPLAIN was considered but is not in the grammar at v0.26.0.
  4. Otherwise WRITE, and run the stop-operations check on the inline text
     as if it were an `exec` script (rules R8, R9).
- **REPL / stdin**: bare `mxcli` with no `-c` is WRITE unconditionally —
  the guard cannot see the statements that will run. If an agent needs to
  run a read query, it must use `-c`.

## Consequences

- Positive: One-liners like `mxcli -c "SHOW modules"` flow through
  cleanly without a dedicated per-command entry.
- Positive: Inline writes get the same stop-op and check-marker treatment
  as scripted writes.
- Negative: Read verbs are grammar-tied; a new DQL statement in a later
  mxcli version needs to be added here before it will work in `-c`.
- Follow-ups: Phase 2+ could ship a tiny MDL tokeniser rather than
  first-word matching, to tolerate leading comments inside statements.

## Versions

- mxcli: pinned at v0.26.0; MDL read-verb set confirmed from grammar at
  SHA `12ce281`.
- Guard: policy/mxcli_guard.py v1.2+.

## References

- ADR-0007, ADR-0011, ADR-0013, ADR-0014.
- `policy/mxcli_guard.py` — `_classify_inline_mdl`, rule R4-c.
