# ADR-0032: The pinned mxcli binary is verified against a recorded SHA-256

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Mendix_Agentic maintainers

## Context

The `mxcli-tree` CI job downloads the pinned mxcli release and runs
`--help` recursively. If the release is republished or redirected to a
different artefact, a silently-swapped binary runs with CI's privileges.
The original job also tried to pick a linux amd64 archive by substring
match — the mxcli v0.26.0 release ships raw ELF binaries, not archives,
so the match failed and the job broke on the first run.

## Decision

- `policy/mxcli-pin.json` records the pinned release details:
  - `version` (`v0.26.0`)
  - `asset` name (`mxcli-linux-amd64`)
  - `download_url` (direct `releases/download/<tag>/<asset>` link)
  - `sha256` of the raw bytes
  - `size_bytes`
- `docs/version-matrix.md` carries the same values for human eyes.
- `.github/scripts/check_mxcli_tree.py` downloads the exact asset,
  computes `sha256`, compares against the pin, and only `chmod +x` + runs
  the binary when both the SHA-256 and the size match. On mismatch, the
  job fails with the expected / actual values and a note that the PR
  should update the pin and justify the change.
- The SHA-256 was computed by the author via `curl -sL -o /tmp/mxcli
  <download_url> && sha256sum /tmp/mxcli` on 2026-10-20. The number lives
  in `policy/mxcli-pin.json` and in this ADR's commit message.
- `GITHUB_TOKEN` is passed to the API/download call to raise rate limits.

## Consequences

- Positive: CI never executes a binary whose bytes we did not inspect.
- Positive: Upgrading the pin is a reviewed PR (new sha256, same path).
- Negative: A republished release breaks CI until the pin is updated.
  Acceptable — "we got a different binary than last time" is exactly the
  thing we want surfaced.
- Follow-ups: Phase 3+ should mirror the asset to a bucket we control so
  CI does not depend on `github.com` uptime for every run.

## Versions

- mxcli: v0.26.0 (per ADR-0013).

## References

- ADR-0007, ADR-0013, ADR-0024.
- `.github/scripts/check_mxcli_tree.py` — `_download_and_verify`.
- `policy/mxcli-pin.json`.
