# ADR-0006: Policy and setup scripts are Python 3 stdlib only

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The guardrail scripts must run on any contributor machine (Windows, macOS,
Linux) and in CI, *before* any package manager has run. Pulling in third-party
dependencies for the guard means the guard can be broken by a missing wheel.

## Decision

`bin/doctor.py`, `policy/mxcli_guard.py` and any phase 1 adapter helpers use
**Python 3.10+ stdlib only** — no `pip install`, no `requirements.txt` for
these scripts, no shell outside what `subprocess` can call portably.

## Consequences

- Positive: Zero-install guard; works on day one on every platform.
- Positive: CI is cheap; no caching or virtualenv dance.
- Negative: No `rich`, no `typer`, no `pydantic` — argparse and `json` only.
- Negative: Some shell interop (quoting on Windows) has to be reimplemented;
  `shlex.split(posix=False)` and friends are our tools.
- Follow-ups: If a later phase needs a non-stdlib library, isolate it in its
  own tool and never let the guard depend on it.

## Versions

- Python: 3.10+ (required for `match` statements, PEP 604 unions).
- All other components: any.

## References

- `AGENTS.md` non-negotiable 5.
- ADR-0005.
