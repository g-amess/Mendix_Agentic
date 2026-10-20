# ADR-0020: Generated adapter output is committed as copies; CI fails on drift

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

Symlinks on Windows need admin privileges and git-level `core.symlinks`
set. A plugin consumed from a marketplace must work on every supported
host without Windows-specific setup. We also want the plugin's contents to
be legible on GitHub, so reviewers can see the generated agent files and
hooks without running the adapter.

## Decision

- The adapter writes **copies** into `plugins/mendix-agentic/`. No
  symlinks.
- Both `plugins/mendix-agentic/policy/` and the main repo's
  `policy/ownership.json` are regenerated on every build.
- `python adapters/claude/build.py --check` builds into a temp dir and
  diffs against the committed output. CI runs it on every PR; a diff fails
  the build.

## Consequences

- Positive: Works on every git host and every OS without extra setup.
- Positive: Reviewers can read `plugins/mendix-agentic/` on GitHub.
- Negative: Doubled bytes for the policy copy. Acceptable for phase 2.
- Follow-ups: If plugin bytes become large, consider a build-time fetch
  from the repository (phase 3+).

## Versions

Applies regardless of version.

## References

- ADR-0005, ADR-0019, ADR-0022.
- `adapters/claude/build.py` — `check`, `_dir_diff`.
