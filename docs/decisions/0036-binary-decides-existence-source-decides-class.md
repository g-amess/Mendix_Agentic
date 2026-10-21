# ADR-0036: The released binary decides which commands exist; source decides their class

- **Status:** Proposed
- **Date:** 2026-10-21
- **Deciders:** Mendix_Agentic maintainers

## Context

The inventory was derived from source (ADR-0012). Source alone cannot say
whether a command is hidden, compiled out by a build tag, or registered only
on some OSes. The `--help` tree of the binary users actually run is the
ground truth for which paths exist. It cannot say what a command writes,
though; only the source can.

During reconciliation, three inventory paths looked absent from the binary.
The cause was our `--help` parser, not mxcli (inventory §8.1). Telling those
cases apart needs an explicit rule.

## Decision

- **Existence:** the pinned release binary's `--help` tree, walked in CI.
- **Class and side effects:** the source at the pinned SHA.
- A path in the inventory but absent from `--help` is an error unless its
  row is marked `hidden: true` or `build_condition: "<condition>"`, with the
  source line that makes it so. CI confirms a `hidden` row by running
  `mxcli <path> --help` (only `--help`/`--version` are ever run).
- At v0.26.0 no row needs either marker: source has no `Hidden: true`, and no
  `//go:build` file registers a command.

## Consequences

- Positive: An absence is either explained in the data or fails CI.
- Negative: CI walks only the Linux asset; an OS-conditional command on
  Windows or macOS would need a `build_condition` row and a manual check.

## Versions

- mxcli: v0.26.0
- Others: any

## References

- ADR-0012, ADR-0024, ADR-0032, ADR-0035.
- `.github/scripts/check_mxcli_tree.py`.
