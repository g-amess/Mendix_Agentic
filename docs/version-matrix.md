# Version matrix

Last reviewed: 2026-10-20. UNVERIFIED entries have not been reconfirmed since
the row was added — rerun the checks before relying on them.

| Component    | Minimum | Tested (target) | Notes                                                                                                       | Verified |
| ------------ | ------- | --------------- | ----------------------------------------------------------------------------------------------------------- | -------- |
| Claude Code  | 2.0     | 2.0+ (any)      | Not required to use this repo; other agents are allowed. Doctor warns if absent.                            | UNVERIFIED |
| mxcli        | v0.26.0 | v0.26.0         | v0.26.0 released 2026-10-11 (github.com/mendixlabs/mxcli/releases). v0.27.0 is newer but out of phase 1 scope. | Y        |
| Studio Pro   | 11.12   | 11.12 LTS       | mxcli refuses writes while `<project>.mpr.lock` is present (cmd_exec.go, see mxcli-inventory.md).           | Y (lock-file check), UNVERIFIED (exact Studio Pro version floor) |
| Python       | 3.10    | 3.10, 3.11, 3.12 | Required for `bin/doctor.py` and `policy/mxcli_guard.py`. Stdlib only (ADR-0006).                           | Y        |
| git          | 2.30    | 2.40+           | Needed for pre-commit hooks and CRLF handling. No lower minimum enforced by `bin/doctor` today.             | UNVERIFIED |

**Note (2026-10-20):** mxcli v0.27.0 was released 2026-10-15 but we remain
pinned at v0.26.0 (ADR-0013). Any upgrade requires re-running
[`docs/research/mxcli-inventory.md`](research/mxcli-inventory.md) and
promoting the policy data (`policy/mxcli-commands.json`) before the pin
moves.

### Pinned mxcli binary (ADR-0032)

| Field       | Value                                                                   |
| ----------- | ----------------------------------------------------------------------- |
| Version     | v0.26.0                                                                 |
| Asset       | `mxcli-linux-amd64` (raw ELF binary, not an archive)                    |
| Size        | 102 301 856 bytes                                                       |
| SHA-256     | `c3fe5450931d52628777107c71617855db6acf606ef7df8815990ac3c55519ea`      |
| Source      | https://github.com/mendixlabs/mxcli/releases/download/v0.26.0/mxcli-linux-amd64 |

The same values live in [`policy/mxcli-pin.json`](../policy/mxcli-pin.json)
and are checked by the `mxcli-tree` CI job before the binary is executed.

## How to update this file

- When a component's floor shifts, add a row and keep the old one with a
  `Superseded by …` note in Notes.
- Pair every change with a `docs/mxcli-bugs.md` entry if it was driven by an
  upstream bug.
- An ADR is required for any change that moves the minimum of mxcli or
  Studio Pro.
