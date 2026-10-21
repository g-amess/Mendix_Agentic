#!/usr/bin/env python3
"""bin/doctor — prerequisite health check for Mendix_Agentic contributors.

Stdlib only (ADR-0006). Each check returns PASS / WARN / FAIL with a
plain-language fix. The script exits 1 if any FAIL is produced, 0 otherwise.
`--json` emits machine-readable output for CI.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

MIN_PYTHON = (3, 10)
MIN_MXCLI = (0, 26, 0)
# ADR-0025: lowest Claude Code with every feature the plugin relies on.
# Evidence per feature is in docs/version-matrix.md.
MIN_CLAUDE_CODE = (2, 1, 281)
CLAUDE_UPDATE_FIX = (
    "run `claude update`; in VS Code also update the extension and restart"
)
# The plugin hook runs `python` (ADR-0026, docs/install.md).
HOOK_PYTHON = "python"

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Result:
    name: str
    status: str  # "PASS" | "WARN" | "FAIL"
    detail: str
    fix: str = ""

    def line(self) -> str:
        tag = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[self.status]
        head = f"{tag} {self.name}: {self.detail}"
        if self.fix and self.status != "PASS":
            head += f"\n       fix: {self.fix}"
        return head


def _run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def _parse_version(s: str) -> tuple[int, ...] | None:
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", s)
    if not m:
        return None
    major, minor, patch = m.group(1), m.group(2), m.group(3) or "0"
    return (int(major), int(minor), int(patch))


def check_python() -> Result:
    v = sys.version_info[:3]
    if v >= MIN_PYTHON + (0,):
        return Result(
            "python",
            "PASS",
            f"Python {v[0]}.{v[1]}.{v[2]} (minimum {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
        )
    return Result(
        "python",
        "FAIL",
        f"Python {v[0]}.{v[1]}.{v[2]} is below minimum {MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
        fix=f"Install Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later from python.org",
    )


def check_git() -> Result:
    if shutil.which("git") is None:
        return Result(
            "git",
            "FAIL",
            "git not on PATH",
            fix="Install git from https://git-scm.com and reopen your shell.",
        )
    rc, out, _ = _run(["git", "--version"])
    if rc != 0:
        return Result("git", "FAIL", "`git --version` failed", fix="Reinstall git.")
    return Result("git", "PASS", out)


def check_mxcli() -> Result:
    if shutil.which("mxcli") is None:
        return Result(
            "mxcli",
            "WARN",
            "mxcli not on PATH",
            fix=(
                "Install mxcli (see github.com/mendixlabs/mxcli). "
                "Not required to work on this repo's docs, but needed before running agents against a project."
            ),
        )
    rc, out, err = _run(["mxcli", "--version"])
    if rc != 0:
        return Result(
            "mxcli",
            "FAIL",
            f"`mxcli --version` returned {rc}: {err or out}",
            fix="Reinstall mxcli from github.com/mendixlabs/mxcli releases.",
        )
    ver = _parse_version(out)
    if ver is None:
        return Result(
            "mxcli",
            "WARN",
            f"could not parse mxcli version from: {out!r}",
            fix="Check `mxcli --version` output format; update bin/doctor.py if upstream changed.",
        )
    if ver < MIN_MXCLI:
        return Result(
            "mxcli",
            "FAIL",
            f"mxcli {'.'.join(map(str, ver))} is below minimum {'.'.join(map(str, MIN_MXCLI))}",
            fix=f"Upgrade mxcli to v{'.'.join(map(str, MIN_MXCLI))} or later.",
        )
    return Result("mxcli", "PASS", f"mxcli {'.'.join(map(str, ver))}")


def check_claude_code() -> Result:
    exe = shutil.which("claude")
    if exe is None:
        return Result(
            "claude-code",
            "WARN",
            "`claude` not on PATH",
            fix=(
                "Install Claude Code if you plan to use it as your agent "
                "(code.claude.com). Other agents are supported — this is not required."
            ),
        )
    rc, out, err = _run(["claude", "--version"])
    if rc != 0 or not out:
        return Result(
            "claude-code",
            "WARN",
            f"`claude --version` returned {rc}: {err or 'empty output'}",
            fix="Ensure Claude Code is up to date (`claude update` or reinstall).",
        )
    return _claude_code_result(out.splitlines()[0])


def _claude_code_result(version_line: str) -> Result:
    minimum = ".".join(map(str, MIN_CLAUDE_CODE))
    ver = _parse_version(version_line)
    if ver is None:
        return Result(
            "claude-code",
            "WARN",
            f"could not parse Claude Code version from: {version_line!r}",
            fix=f"Check that Claude Code is {minimum} or later; {CLAUDE_UPDATE_FIX}.",
        )
    if ver < MIN_CLAUDE_CODE:
        return Result(
            "claude-code",
            "FAIL",
            f"Claude Code {'.'.join(map(str, ver))} is below minimum {minimum}",
            fix=CLAUDE_UPDATE_FIX + ".",
        )
    return Result("claude-code", "PASS", f"{version_line} (minimum {minimum})")


def check_hook_python() -> Result:
    """The plugin hook invokes `python`; it must resolve to >= MIN_PYTHON.

    Doctor itself may run under `py -3` (bin/doctor.cmd), so this checks the
    hook's interpreter separately. A missing or too-old `python` blocks every
    guarded tool call (ADR-0026), so it is a FAIL when Claude Code is present.
    """
    status_if_bad = "FAIL" if shutil.which("claude") else "WARN"
    minimum = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    fix = (
        f"Install Python {minimum}+ so `{HOOK_PYTHON}` is on PATH (python.org "
        "installer: tick \"Add python.exe to PATH\"; on Windows also turn off the "
        "python App execution aliases). See docs/install.md."
    )
    if shutil.which(HOOK_PYTHON) is None:
        return Result("hook-python", status_if_bad, f"`{HOOK_PYTHON}` not on PATH", fix=fix)
    rc, out, err = _run(
        [HOOK_PYTHON, "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"]
    )
    ver = _parse_version(out) if rc == 0 else None
    if ver is None:
        return Result(
            "hook-python",
            status_if_bad,
            f"`{HOOK_PYTHON}` did not report a version (rc={rc}: {err or out or 'no output'})",
            fix=fix,
        )
    if ver < MIN_PYTHON + (0,):
        return Result(
            "hook-python",
            status_if_bad,
            f"`{HOOK_PYTHON}` is {'.'.join(map(str, ver))}, below {minimum}",
            fix=fix,
        )
    return Result("hook-python", "PASS", f"`{HOOK_PYTHON}` is {'.'.join(map(str, ver))}")


def check_line_endings() -> Result:
    if shutil.which("git") is None:
        return Result(
            "line-endings",
            "WARN",
            "git not available, cannot inspect core.autocrlf",
            fix="Install git.",
        )
    rc, out, _ = _run(["git", "config", "--get", "core.autocrlf"])
    autocrlf = out.lower() if rc == 0 else "(unset)"
    gitattr = REPO_ROOT / ".gitattributes"
    attr_ok = gitattr.exists() and "eol=lf" in gitattr.read_text(encoding="utf-8")
    if attr_ok:
        return Result(
            "line-endings",
            "PASS",
            f".gitattributes pins eol=lf; git core.autocrlf={autocrlf}",
        )
    return Result(
        "line-endings",
        "WARN",
        f".gitattributes missing or does not pin eol=lf (core.autocrlf={autocrlf})",
        fix="Keep `.gitattributes` with `* text=auto eol=lf`.",
    )


_CRLF_GLOBS = ("*.sh", "*.py")
_SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".research",  # upstream clones, read-only reference material
    ".mxagent",   # guard-managed state
}


def check_studio_pro_override_env() -> Result:
    """FAIL if MXCLI_ALLOW_STUDIO_PRO_OPEN is set — it disables mxcli's lock-file safety."""
    val = os.environ.get("MXCLI_ALLOW_STUDIO_PRO_OPEN")
    if val is None or val == "":
        return Result(
            "studio-pro-override",
            "PASS",
            "MXCLI_ALLOW_STUDIO_PRO_OPEN is not set",
        )
    return Result(
        "studio-pro-override",
        "FAIL",
        f"MXCLI_ALLOW_STUDIO_PRO_OPEN={val!r} is set in this shell",
        fix=(
            "Unset it (`unset MXCLI_ALLOW_STUDIO_PRO_OPEN` on posix; "
            "`Remove-Item Env:MXCLI_ALLOW_STUDIO_PRO_OPEN` on PowerShell). "
            "It disables mxcli's Studio Pro lock-file check (ADR-0011)."
        ),
    )


def check_no_crlf_in_scripts() -> Result:
    offenders: list[str] = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            if not any(_match_glob(name, g) for g in _CRLF_GLOBS):
                continue
            p = Path(root) / name
            try:
                with open(p, "rb") as fh:
                    chunk = fh.read(65536)
            except OSError:
                continue
            if b"\r\n" in chunk:
                offenders.append(str(p.relative_to(REPO_ROOT)))
    if not offenders:
        return Result("no-crlf", "PASS", "no CRLF in *.sh/*.py")
    return Result(
        "no-crlf",
        "FAIL",
        f"CRLF found in: {', '.join(sorted(offenders)[:5])}"
        + (" …" if len(offenders) > 5 else ""),
        fix=(
            "Normalise line endings: `git add --renormalize .` and commit. "
            "Confirm `.gitattributes` has `* text=auto eol=lf`."
        ),
    )


def _match_glob(name: str, pattern: str) -> bool:
    import fnmatch

    return fnmatch.fnmatchcase(name, pattern)


CHECKS = (
    check_python,
    check_git,
    check_mxcli,
    check_claude_code,
    check_hook_python,
    check_line_endings,
    check_no_crlf_in_scripts,
    check_studio_pro_override_env,
)


def run() -> list[Result]:
    return [c() for c in CHECKS]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mendix_Agentic prerequisite checker.")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args(argv)

    results = run()
    if args.json:
        payload = {
            "results": [asdict(r) for r in results],
            "exit": 1 if any(r.status == "FAIL" for r in results) else 0,
        }
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            print(r.line())
        summary = {s: sum(1 for r in results if r.status == s) for s in ("PASS", "WARN", "FAIL")}
        print(f"\nSummary: PASS {summary['PASS']}  WARN {summary['WARN']}  FAIL {summary['FAIL']}")

    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
