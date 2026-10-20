# Threat model

The `mxcli_guard` is a seat belt, not a vault. It assumes an agent that is
usually honest and occasionally wrong — not one that is trying to break out.

## What the guard protects against

- **Agent mistakes.** The commonest failure is an agent asking to run a
  destructive mxcli write (`exec`, `rename`, `fix`) without the SHOW /
  DESCRIBE / draft / check / approve sequence. Rules R2, R2a, R4, R5, R8, R9
  stop that path.
- **Drift between the installed mxcli and our policy data.** The guard
  treats unknown or unverified rows as WRITE (ADR-0007), and unlisted
  children of listed parents are also WRITE (ADR-0014), so a surprise new
  subcommand after an upgrade fails safely.
- **Accidental writes to the model while Studio Pro has it open.** Rule R6
  honours `<project>.mpr.lock`; override flags and env vars are refused
  (ADR-0011).
- **Overwriting an unversioned model.** Rule R7a (fail-closed) requires git
  and a worktree before any WRITE; rule R7 refuses to run against a dirty
  `.mpr` or `mprcontents/`.
- **Agents overwriting the guard itself.** Rules R2a / R2b forbid tool
  calls that touch `.mxagent/**` or `policy/**` — the only way those files
  change is a reviewed git commit on `main`.

## What the guard does NOT protect against

- **A deliberately obfuscating agent.** PowerShell `Invoke-Expression`,
  base64 payloads, remote shells, process-level forks — these can be
  worked around. Rule R2d is a backstop, not a solution: it denies the
  constructs we have seen agents reach for, but assumes Bash is the
  sanctioned shell (ADR-0016).
- **Supply-chain attacks on mxcli itself.** If a tampered mxcli binary is
  on `$PATH`, no shell-level policy helps.
- **Malicious contributors.** Someone who can edit `policy/**` on `main`
  has already bypassed every rule. Branch protection and reviewed PRs
  (ADR-0009) are the control.
- **Local DB mutations through `mxcli sql`.** We classify `sql` as WRITE,
  but mxcli itself does not inspect the query.

## Backstops that catch what the guard misses

1. **Git snapshots.** Every WRITE runs against a committed `.mpr`; recovery
   is `git restore`. ADR-0004 and ADR-0010.
2. **mxcli's own Studio Pro lock check.** Even if the guard let a write
   through, mxcli itself refuses on the lock (we additionally deny the
   override, ADR-0011).
3. **Human approval gates.** `mxcli check` runs before `mxcli exec`, and
   the designated writer runs only when ownership is explicit (phase 1
   ships ownership empty).
4. **CI.** Doctor and the test suite run on every push and PR
   (ADR-0009); drift in `policy/mxcli-commands.json` is caught by the
   inventory-consistency test.

See `AGENTS.md` for the contributor rules that complement these controls,
and `docs/decisions/` for the ADRs this file references.
