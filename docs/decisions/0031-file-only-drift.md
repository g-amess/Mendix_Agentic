# ADR-0031: Drift checks compare tracked files only; no empty directories

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The first version of `adapters/claude/build.py --check` compared
directories (via `filecmp.dircmp`). It emitted empty `agents/` and
`skills/` directories when there were no roles or skills in `core/`. Git
cannot track empty directories, so a clean `git clone` of the branch
produced "generated plugin output drifts from committed: agents (only in
generated), skills (only in generated)" and every CI matrix job failed.

The committed tree and the generated tree have to match byte-for-byte
using only what git tracks — which is files.

## Decision

- `--check` compares only the set of **files** (relative paths + byte
  content). Directories are ignored.
- The build never emits an empty directory. If a role list is empty,
  the `agents/` directory is not created. Same for `skills/`.
- File comparison is byte-exact *after* normalising `\r\n → \n`, so a
  Windows checkout with `core.autocrlf` expansion still matches a Linux
  build. The build writes LF-only via `_write_text_lf`.
- Generated output must contain **no** absolute paths, usernames,
  timestamps, or machine-specific values. The build is reproducible: two
  runs into different temp directories produce identical bytes.
- If a plugin component ever requires a directory to exist even when
  empty, add a tracked placeholder (e.g. `.gitkeep`) and document why in
  that directory's README. Phase 2 did not need one.

## Consequences

- Positive: `--check` passes on a clean clone on every CI matrix.
- Positive: Drift is a byte-level answer, not an fs-level answer; CRLF
  expansion on Windows no longer causes false failures.
- Negative: A reviewer who expects `agents/` to always exist is surprised
  when the dir is absent — the alternative was CI red every push.
- Follow-ups: Phase 3+ ships real role cards and the `agents/` dir
  reappears automatically.

## Versions

Applies regardless of version.

## References

- `adapters/claude/build.py` — `_list_files`, `_read_bytes_lf`,
  `_dir_diff`, `_write_text_lf`.
- ADR-0020.
