#!/usr/bin/env python3
"""Render the command tables in docs/research/mxcli-inventory.md §2 from
policy/mxcli-commands.json (ADR-0035). The JSON is the source of record; the
markdown between the GENERATED markers is never hand-edited.

Usage:
    python .github/scripts/render_mxcli_inventory.py          # rewrite in place
    python .github/scripts/render_mxcli_inventory.py --check  # exit 1 on drift
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_JSON = REPO_ROOT / "policy" / "mxcli-commands.json"
INVENTORY_MD = REPO_ROOT / "docs" / "research" / "mxcli-inventory.md"

BEGIN = "<!-- BEGIN GENERATED from policy/mxcli-commands.json by .github/scripts/render_mxcli_inventory.py; do not edit -->"
END = "<!-- END GENERATED -->"

_SOURCE_LABEL_RE = re.compile(r"^https://github\.com/mendixlabs/mxcli/blob/[^/]+/(.+)$")


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _source(src: str) -> str:
    m = _SOURCE_LABEL_RE.match(src)
    if m:
        return f"[{m.group(1)}]({src})"
    return _cell(src)


def _row(path: str, row: dict) -> str:
    verified = "Y" if row.get("verified") is True else "UNVERIFIED"
    effects = ", ".join(row.get("side_effects", [])) or "—"
    notes = row.get("notes", "")
    flags = []
    if row.get("hidden"):
        flags.append("**Hidden** (absent from --help)")
    if row.get("build_condition"):
        flags.append(f"**Build condition:** `{row['build_condition']}`")
    notes = " ".join(flags + ([notes] if notes else []))
    return (
        f"| `{path}` | {row['class']} | {verified} | {effects} | "
        f"{_source(row.get('source', ''))} | {_cell(notes)} |"
    )


_HEADER = (
    "| Command | Class | Verified | Side effects | Source | Notes |\n"
    "|---|---|---|---|---|---|"
)


def render(commands: dict) -> str:
    top = [k for k in commands if " " not in k]
    parents = sorted(t for t in top if any(k.startswith(t + " ") for k in commands))
    out = [BEGIN, "", "### 2.1 Root commands", "", _HEADER]
    out += [_row(k, commands[k]) for k in top]
    for n, parent in enumerate(parents, start=2):
        out += ["", f"### 2.{n} `{parent}` subtree", "", _HEADER]
        out.append(_row(parent, commands[parent]))
        out += [_row(k, commands[k]) for k in commands if k.startswith(parent + " ")]
    out += ["", END]
    return "\n".join(out)


def apply(md: str, block: str) -> str:
    start = md.index(BEGIN)
    end = md.index(END) + len(END)
    return md[:start] + block + md[end:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if the markdown is stale")
    args = ap.parse_args(argv)
    commands = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))["commands"]
    md = INVENTORY_MD.read_text(encoding="utf-8")
    new = apply(md, render(commands))
    if args.check:
        if new != md:
            print(
                "ERROR: docs/research/mxcli-inventory.md §2 is stale. Run "
                "`python .github/scripts/render_mxcli_inventory.py` and commit.",
                file=sys.stderr,
            )
            return 1
        print("OK: inventory tables match policy/mxcli-commands.json.")
        return 0
    INVENTORY_MD.write_bytes(new.encode("utf-8"))
    print(f"OK: rendered {len(commands)} command rows into {INVENTORY_MD.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
