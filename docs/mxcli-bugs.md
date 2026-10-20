# mxcli bug ledger

One row per upstream bug we have hit. Keep closed/fixed rows; delete only if
they turn out to have been user error. `Retested on` is the last mxcli
version where someone actually ran the reproduction and confirmed the state
(fixed / still broken / changed).

| ID    | mxcli version | Mendix version | Symptom                                              | Workaround                                                                                        | Retested on | Status  |
| ----- | ------------- | -------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------- | ------- |
| MX-0001 **EXAMPLE** | v0.00.0       | 0.0.0          | **EXAMPLE ROW — remove when the first real bug lands.** Describe the smallest reproduction here. | Describe the workaround in one sentence. Link to the upstream issue if one exists.                 | v0.00.0     | EXAMPLE |

## Columns

- **ID** — `MX-NNNN`, four-digit, next free.
- **mxcli version** — the version where the symptom was first observed.
- **Mendix version** — the Mendix (Studio Pro / runtime) version in play.
- **Symptom** — what the user saw. One sentence.
- **Workaround** — what to do until fixed. If there is no workaround, say so.
- **Retested on** — the mxcli version used in the most recent retest.
- **Status** — `Open`, `Fixed`, `Won't fix`, or `EXAMPLE`.
