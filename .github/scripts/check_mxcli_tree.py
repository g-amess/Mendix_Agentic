#!/usr/bin/env python3
"""Check an installed mxcli binary's command tree against policy/mxcli-commands.json.

Downloads the pinned v0.26.0 Linux release asset from
https://api.github.com/repos/mendixlabs/mxcli/releases/tags/v0.26.0, runs
`mxcli --help` recursively, and fails if the discovered command paths
disagree with the inventory.

Usage (CI):
    python .github/scripts/check_mxcli_tree.py --tag v0.26.0
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _github(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.loads(fh.read())


def _find_linux_asset(release: dict) -> str:
    """Pick the linux-amd64 tarball or zip from the release assets."""
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        n = name.lower()
        if ("linux" in n and ("amd64" in n or "x86_64" in n)
                and (n.endswith(".tar.gz") or n.endswith(".tgz") or n.endswith(".zip"))):
            return asset["browser_download_url"]
    raise SystemExit(
        f"ERROR: no linux amd64 asset in release. Assets: {[a.get('name') for a in release.get('assets', [])]}"
    )


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as fh:
        dest.write_bytes(fh.read())


def _extract_binary(archive: Path, out_dir: Path) -> Path:
    """Extract and return the path to the mxcli binary inside `out_dir`."""
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(out_dir)
    else:
        with tarfile.open(archive, "r:*") as tf:
            tf.extractall(out_dir)
    for p in out_dir.rglob("mxcli"):
        if p.is_file() and os.access(p, os.X_OK) or p.name == "mxcli":
            p.chmod(0o755)
            return p
    raise SystemExit("ERROR: could not find `mxcli` binary in extracted release")


_USAGE_SUB_RE = re.compile(r"^\s{2,}(\S+)(?:\s{2,}|$)")


def _list_subcommands(binary: Path, prefix: list[str]) -> list[str]:
    """Run `mxcli <prefix...> --help` and return the direct subcommand names."""
    cmd = [str(binary), *prefix, "--help"]
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise SystemExit(f"ERROR: cannot invoke {cmd[0]!r}")
    output = (p.stdout or "") + "\n" + (p.stderr or "")
    # Collect the lines under an "Available Commands:" or "Commands:" block.
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
                subs.append(m.group(1))
    return subs


def _walk_tree(binary: Path) -> set[str]:
    """BFS the command tree and return every path as 'parent child child2'."""
    seen: set[str] = set()
    stack: list[list[str]] = [[]]  # start at root
    while stack:
        prefix = stack.pop()
        subs = _list_subcommands(binary, prefix)
        for s in subs:
            path = prefix + [s]
            seen.add(" ".join(path))
            stack.append(path)
    return seen


def _load_inventory_keys() -> set[str]:
    data = json.loads((REPO_ROOT / "policy" / "mxcli-commands.json").read_text(encoding="utf-8"))
    return set(data["commands"].keys())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag", default="v0.26.0")
    args = ap.parse_args(argv)
    tag = args.tag

    print(f"Fetching release {tag} from mendixlabs/mxcli …")
    release = _github(f"https://api.github.com/repos/mendixlabs/mxcli/releases/tags/{tag}")
    asset_url = _find_linux_asset(release)
    print(f"Found linux asset: {asset_url}")

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        archive = tdp / "mxcli-release" + Path(asset_url).suffix
        archive = Path(str(archive))
        _download(asset_url, archive)
        extract_dir = tdp / "extracted"
        extract_dir.mkdir()
        binary = _extract_binary(archive, extract_dir)
        print(f"Extracted mxcli to {binary}")

        discovered = _walk_tree(binary)
        inventory = _load_inventory_keys()
        # The inventory contains alias rows (`list`) and some entries that
        # mxcli does not surface in --help (`help`). Filter those out before
        # the diff.
        aliases = {"list"}
        inventory_cmp = {k for k in inventory if k not in aliases and k != "help"}

        missing = sorted(discovered - inventory_cmp)
        extra = sorted(inventory_cmp - discovered)
        if missing:
            print(
                f"\nERROR: {len(missing)} command(s) in mxcli but not in inventory:",
                file=sys.stderr,
            )
            for m in missing:
                print(f"  + {m}", file=sys.stderr)
        if extra:
            print(
                f"\nERROR: {len(extra)} command(s) in inventory but not in mxcli:",
                file=sys.stderr,
            )
            for e in extra:
                print(f"  - {e}", file=sys.stderr)
        if missing or extra:
            print(
                "\nUpdate docs/research/mxcli-inventory.md and "
                "policy/mxcli-commands.json, then rerun.",
                file=sys.stderr,
            )
            return 1
    print(f"OK: {len(discovered)} commands match inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
