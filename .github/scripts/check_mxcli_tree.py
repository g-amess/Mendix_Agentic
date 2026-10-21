#!/usr/bin/env python3
"""Check an installed mxcli binary's command tree against policy/mxcli-commands.json.

Downloads the raw binary from the pinned release (per policy/mxcli-pin.json,
ADR-0032), verifies its SHA-256 against the pin, and runs `mxcli --help`
recursively over the command tree. Fails if the discovered command paths
disagree with the inventory.

Usage (CI):
    python .github/scripts/check_mxcli_tree.py --cache-dir ~/.cache/mxcli

Env:
    GITHUB_TOKEN   optional; raises the GitHub API rate limit when fetching
                   release metadata (we only download the asset directly,
                   so it is not strictly required, but the CI job sets it
                   anyway).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIN_PATH = REPO_ROOT / "policy" / "mxcli-pin.json"
INVENTORY_PATH = REPO_ROOT / "policy" / "mxcli-commands.json"


def _load_pin() -> dict:
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))["pin"]


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if "api.github.com" in url:
        req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=60) as fh:
        return fh.read()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _obtain_verified(pin: dict, dest: Path) -> None:
    """Make `dest` hold the pinned binary, verified. A cached copy (CI
    restores one from actions/cache) is re-hashed before use; on mismatch it
    is discarded and the asset downloaded again (ADR-0032)."""
    if dest.exists():
        data = dest.read_bytes()
        if _sha256(data) == pin["sha256"] and len(data) == pin.get("size_bytes", len(data)):
            dest.chmod(0o755)
            print(f"Cache hit: verified sha256={pin['sha256']} ({len(data)} bytes) -> {dest}")
            return
        print(f"Cached {dest} does not match the pin; downloading again.")
        dest.unlink()
    _download_and_verify(pin, dest)


def _download_and_verify(pin: dict, dest: Path) -> None:
    url = pin["download_url"]
    print(f"Downloading {pin['asset']} from {url}")
    data = _http_get(url)
    actual = _sha256(data)
    expected = pin["sha256"]
    if actual != expected:
        raise SystemExit(
            "ERROR: sha256 mismatch; refusing to execute an unverified binary.\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}\n"
            f"  bytes:    {len(data)}\n"
            f"  pinned:   {pin.get('size_bytes', '?')}\n"
            "If the upstream release was republished, update "
            "policy/mxcli-pin.json with the new sha256 (and justify the "
            "change in the PR)."
        )
    size_expected = pin.get("size_bytes")
    if size_expected is not None and len(data) != size_expected:
        raise SystemExit(
            f"ERROR: size mismatch - got {len(data)} bytes, pinned "
            f"{size_expected}. Update policy/mxcli-pin.json."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    dest.chmod(0o755)
    print(f"Verified sha256={actual} ({len(data)} bytes) -> {dest}")


# cobra pads each name to the longest name in the block (minimum 11) and
# then prints ONE space before the Short text, so the longest name of 11+
# characters is followed by a single space. Requiring two spaces there
# silently dropped e.g. `extract-templates`, `diag session-report`,
# `mcp capabilities` and `fix design-properties` (phase 2.2).
_USAGE_SUB_RE = re.compile(r"^\s{2,}(\S+)(?:\s|$)")


def _list_subcommands(binary: Path, prefix: list[str]) -> list[str]:
    cmd = [str(binary), *prefix, "--help"]
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except FileNotFoundError:
        raise SystemExit(f"ERROR: cannot invoke {cmd[0]!r}")
    output = (p.stdout or "") + "\n" + (p.stderr or "")
    subs: list[str] = []
    in_block = False
    for line in output.splitlines():
        if re.match(r"^(Available Commands|Commands):\s*$", line.strip()):
            in_block = True
            continue
        if in_block:
            if not line.strip():
                break
            m = _USAGE_SUB_RE.match(line)
            if m:
                name = m.group(1)
                # cobra prints `help` on every parent; skip it.
                if name == "help":
                    continue
                subs.append(name)
    return subs


def _hidden_help_ok(binary: Path, path: str) -> bool:
    p = subprocess.run(
        [str(binary), *path.split(), "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    return p.returncode == 0 and f"mxcli {path}" in p.stdout


def _walk_tree(binary: Path) -> set[str]:
    seen: set[str] = set()
    stack: list[list[str]] = [[]]
    while stack:
        prefix = stack.pop()
        subs = _list_subcommands(binary, prefix)
        for s in subs:
            path = prefix + [s]
            seen.add(" ".join(path))
            stack.append(path)
    return seen


def _load_inventory() -> dict[str, dict]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))["commands"]


def _may_be_absent(row: dict) -> bool:
    """ADR-0036: only rows marked hidden or build-conditional may be missing
    from the --help tree."""
    return bool(row.get("hidden")) or bool(row.get("build_condition"))


def compare(discovered: set[str], inventory: dict[str, dict]) -> tuple[list[str], list[str], list[str]]:
    """Return (missing from inventory, extra in inventory, excused absences)."""
    # `list` is an alias of `show`; cobra's --help does not list aliases.
    # The built-in `help` command is filtered in _list_subcommands.
    skip = {"list", "help"}
    inv = {k: v for k, v in inventory.items() if k not in skip}
    missing = sorted(discovered - set(inv))
    absent = sorted(set(inv) - discovered)
    excused = [k for k in absent if _may_be_absent(inv[k])]
    extra = [k for k in absent if not _may_be_absent(inv[k])]
    return missing, extra, excused


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--cache-dir",
        help="keep the verified binary here between runs (CI restores it "
        "with actions/cache); it is re-hashed against the pin before use",
    )
    args = ap.parse_args(argv)

    pin = _load_pin()
    print(f"Pinned mxcli: {pin['version']} ({pin['asset']})")

    with tempfile.TemporaryDirectory() as td:
        base = Path(args.cache_dir) if args.cache_dir else Path(td)
        binary = base / pin["asset"]
        _obtain_verified(pin, binary)
        return _compare(binary)


def _compare(binary: Path) -> int:
    discovered = _walk_tree(binary)
    inventory = _load_inventory()
    missing, extra, excused = compare(discovered, inventory)
    for k in excused:
        row = inventory[k]
        if row.get("hidden"):
            # A hidden cobra command still answers `<path> --help`; a path
            # that does not exist falls through to its parent's help or
            # errors, so check the usage line names the path.
            if _hidden_help_ok(binary, k):
                print(f"note: {k} is hidden; confirmed with `mxcli {k} --help`")
            else:
                print(
                    f"ERROR: {k} is marked hidden but `mxcli {k} --help` does not answer for it",
                    file=sys.stderr,
                )
                extra.append(k)
        else:
            print(f"note: {k} absent from --help (build_condition {row['build_condition']!r}); allowed")
    if missing:
        print(
            f"\nERROR: {len(missing)} command(s) in mxcli but not in inventory:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"  + {m}", file=sys.stderr)
    if extra:
        print(
            f"\nERROR: {len(extra)} command(s) in inventory but not in mxcli "
            "(and not marked hidden or build_condition):",
            file=sys.stderr,
        )
        for e in extra:
            print(f"  - {e}", file=sys.stderr)
    if missing or extra:
        print(
            "\nUpdate policy/mxcli-commands.json, run "
            ".github/scripts/render_mxcli_inventory.py, then rerun.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(discovered)} commands match inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
