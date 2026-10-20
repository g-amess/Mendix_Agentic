# ADR-0007: Unknown or unverified mxcli commands are treated as writes

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

mxcli is young and moves fast. New subcommands land in minor releases. If the
guard defaults to "allow" for anything it does not recognise, the first thing
an agent will do is reach for the newest command and bypass the guardrail.

## Decision

The guard treats a mxcli command as **WRITE** when it is:

- not listed in `policy/mxcli-commands.json`, or
- listed with `verified: false`, or
- listed with class `UNKNOWN`.

Promoting a command to READ requires an inventory entry with a source link
to `mendixlabs/mxcli` at a specific commit, or to the `mxcli.org` docs, and
`verified: true`.

## Consequences

- Positive: Fails safe when upstream adds surface area.
- Positive: Creates pressure to keep the inventory current.
- Negative: Agents are briefly blocked after an mxcli upgrade until someone
  classifies the new command.
- Follow-ups: `bin/doctor` or a new `bin/inventory-check` could warn when
  installed mxcli emits a subcommand missing from the inventory.

## Versions

- mxcli: any (policy is version-agnostic; the data file is per-version).
- All other components: any.

## References

- `AGENTS.md` non-negotiable 1.
- ADR-0005.
