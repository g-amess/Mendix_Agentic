#!/usr/bin/env python3
"""adapters/claude/build.py — build the mendix-agentic Claude Code plugin.

Reads canonical content from `core/` and `policy/`, writes the Claude Code
plugin layout into `plugins/mendix-agentic/`. Stdlib only (ADR-0006).

Modes:
    python adapters/claude/build.py             # build in place
    python adapters/claude/build.py --check     # build into a temp dir and
                                                # diff against the committed
                                                # output; exit 1 on drift
    python adapters/claude/build.py --out DIR   # build into DIR

The adapter also emits two side artefacts:
- `plugins/mendix-agentic/policy/ownership.json` — generated from role
  `owns` fields (ADR-0019). Marked GENERATED.
- `adapters/claude/out/project-settings.json` — template for downstream
  Mendix projects (not applied here; phase 6+).

Plugin subagents ignore `hooks`, `mcpServers`, and `permissionMode` per the
Claude Code plugin docs, so the adapter does not emit them.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from adapters.lib.frontmatter import parse_frontmatter, FrontmatterError  # noqa: E402

ADAPTER_DIR = Path(__file__).resolve().parent
PLUGIN_NAME = "mendix-agentic"
DEFAULT_OUT = REPO_ROOT / "plugins" / PLUGIN_NAME
PROJECT_SETTINGS_OUT = ADAPTER_DIR / "out" / "project-settings.json"

# Claude-only skill fields an `adapter.claude.json` sidecar may set, in
# emission order (code.claude.com/docs/en/skills, frontmatter reference).
CLAUDE_SKILL_FIELDS = (
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "context",
    "agent",
    "paths",
)

GENERATED_HEADER = (
    "GENERATED FROM core/ BY adapters/claude/build.py — DO NOT EDIT.\n"
    "Regenerate with: `python adapters/claude/build.py`."
)


# -----------------------------------------------------------------------------
# Loaders
# -----------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_version(repo_root: Path) -> str:
    v = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
    if not v:
        raise RuntimeError("VERSION file is empty")
    return v


def _load_capability_map() -> dict:
    return _load_json(ADAPTER_DIR / "capability-map.json")


def _load_roles(core_dir: Path) -> list[dict]:
    roles: list[dict] = []
    rd = core_dir / "roles"
    if not rd.exists():
        return roles
    for p in sorted(rd.glob("*.md")):
        if p.name == "README.md":
            continue
        text = p.read_text(encoding="utf-8")
        try:
            parsed = parse_frontmatter(text, filename=str(p))
        except FrontmatterError as e:
            raise SystemExit(f"ERROR: {e}")
        body = "\n".join(text.splitlines()[parsed.body_start_line - 1 :])
        roles.append({"path": p, "frontmatter": parsed.data, "body": body})
    return roles


def _load_skills(core_dir: Path) -> list[dict]:
    skills: list[dict] = []
    sd = core_dir / "skills"
    if not sd.exists():
        return skills
    for skill_md in sorted(sd.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        try:
            parsed = parse_frontmatter(text, filename=str(skill_md))
        except FrontmatterError as e:
            raise SystemExit(f"ERROR: {e}")
        body = "\n".join(text.splitlines()[parsed.body_start_line - 1 :])
        sidecar = skill_md.parent / "adapter.claude.json"
        extras = _load_json(sidecar) if sidecar.exists() else {}
        skills.append({
            "path": skill_md,
            "folder": skill_md.parent,
            "frontmatter": parsed.data,
            "body": body,
            "claude_extras": extras,
        })
    return skills


# -----------------------------------------------------------------------------
# Frontmatter emitters
# -----------------------------------------------------------------------------

def _emit_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        if v == "" or re.search(r"[\s:#'\",\[\]{}]", v):
            # quote strings with whitespace or structural chars
            escaped = v.replace('"', '\\"')
            return f'"{escaped}"'
        return v
    raise TypeError(f"cannot emit scalar of type {type(v).__name__}")


_PLAIN_UNSAFE_START = tuple("[]{}&*!|>'\"%@`,#?-:")


def _emit_plain(v: str) -> str:
    """Emit a block-context YAML plain scalar when that is unambiguous,
    otherwise fall back to `_emit_scalar` quoting.

    Used for comma-separated tool strings (ADR-0028): commas and brackets
    are only special inside YAML flow collections, so
    `Read, Grep, Agent(a, b)` is a single plain scalar in block context.
    """
    if (
        v
        and v == v.strip()
        and not v.startswith(_PLAIN_UNSAFE_START)
        and ": " not in v
        and " #" not in v
        and not v.endswith(":")
    ):
        return v
    return _emit_scalar(v)


def _tools_string(tools: list[str]) -> str:
    """Comma-separated tool list per the subagent docs (ADR-0028).

    Never a YAML flow list: a flow list splits `Agent(a, b)` on the comma.
    """
    return ", ".join(tools)


def _emit_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if key == "tools" and isinstance(value, str):
            lines.append(f"{key}: {_emit_plain(value)}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            elif all(isinstance(x, (str, int, bool)) for x in value):
                # Prefer flow form for compactness, scalar items only.
                items = ", ".join(_emit_scalar(x) for x in value)
                lines.append(f"{key}: [{items}]")
            else:
                raise TypeError(f"only scalar lists are supported in frontmatter: {key}")
        else:
            lines.append(f"{key}: {_emit_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# -----------------------------------------------------------------------------
# Role → subagent markdown
# -----------------------------------------------------------------------------

def _role_to_subagent(
    role: dict, roles_by_name: dict[str, dict], capability_map: dict
) -> tuple[str, str]:
    fm = role["frontmatter"]
    body = role["body"]
    name = fm["name"]

    tools: list[str] = []
    seen: set[str] = set()
    cap_to_tools: dict[str, list[str]] = capability_map["capability_to_tools"]
    for cap in fm.get("capabilities", []):
        for t in cap_to_tools.get(cap, []):
            if t not in seen:
                seen.add(t)
                tools.append(t)
    # delegate → Agent(<plugin>:<spoke>, …). Plugin agents are registered
    # under their namespaced name; on Claude Code 2.1.305 an allowlist entry
    # of the bare name matches nothing (docs/install.md, ADR-0028).
    if "delegate" in fm.get("capabilities", []):
        delegates = fm.get("delegates_to", [])
        if delegates:
            agent_tool = (
                "Agent("
                + ", ".join(f"{PLUGIN_NAME}:{d}" for d in sorted(delegates))
                + ")"
            )
            if agent_tool not in seen:
                seen.add(agent_tool)
                tools.append(agent_tool)

    model = capability_map["model_tier_to_alias"].get(fm["model_tier"], "sonnet")

    sub_fm: dict[str, Any] = {
        "name": name,
        "description": fm["description"],
        "tools": _tools_string(tools),
        "model": model,
    }
    skills = fm.get("skills", [])
    if skills:
        sub_fm["skills"] = skills
    color = capability_map.get("subagent_color_default")
    if color:
        sub_fm["color"] = color

    md = _emit_frontmatter(sub_fm) + "\n" + body
    if not md.endswith("\n"):
        md += "\n"
    return name, md


# -----------------------------------------------------------------------------
# Skill: copy + merge sidecar
# -----------------------------------------------------------------------------

def _write_skill(skill: dict, out_root: Path) -> None:
    name = skill["frontmatter"]["name"]
    dest = out_root / "skills" / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    merged_fm = dict(skill["frontmatter"])
    # Claude-only fields go top-level (ADR-0027): Claude Code reads
    # `disable-model-invocation` etc. only there, never under `metadata`.
    # The canonical core SKILL.md stays spec-only.
    extras = skill["claude_extras"]
    for key in CLAUDE_SKILL_FIELDS:
        if key not in extras:
            continue
        if key in merged_fm:
            raise SystemExit(
                f"ERROR: {skill['path']}: {key!r} is set in both SKILL.md and "
                "adapter.claude.json; keep it in one place."
            )
        merged_fm[key] = extras[key]
    unknown = set(extras) - set(CLAUDE_SKILL_FIELDS)
    if unknown:
        raise SystemExit(
            f"ERROR: {skill['folder'] / 'adapter.claude.json'}: unknown keys "
            f"{sorted(unknown)}; allowed: {list(CLAUDE_SKILL_FIELDS)}"
        )
    # Rewrite SKILL.md
    body = skill["body"]
    skill_md = _emit_skill_frontmatter(merged_fm) + "\n" + body
    if not skill_md.endswith("\n"):
        skill_md += "\n"
    (dest / "SKILL.md").write_text(skill_md, encoding="utf-8")
    # Copy sidecar directories (scripts/, references/, assets/)
    for sub in ("scripts", "references", "assets"):
        src = skill["folder"] / sub
        if src.exists():
            shutil.copytree(src, dest / sub)


def _emit_skill_frontmatter(data: dict[str, Any]) -> str:
    """Skill frontmatter supports a nested `metadata` mapping of str→str."""
    lines = ["---"]
    for key, value in data.items():
        if key == "metadata" and isinstance(value, dict):
            lines.append("metadata:")
            for k, v in value.items():
                lines.append(f"  {k}: {_emit_scalar(str(v))}")
        elif isinstance(value, list):
            # Block lists: items such as `Bash(git add:*)` or `**/*.{ts,tsx}`
            # contain spaces and commas, which a flow list or a
            # comma-separated string would split.
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                lines.extend(f"  - {_emit_scalar(x)}" for x in value)
        else:
            lines.append(f"{key}: {_emit_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# -----------------------------------------------------------------------------
# Plugin README (generated; the plugin dir is wiped on every build)
# -----------------------------------------------------------------------------

def _plugin_readme() -> str:
    return (
        "# mendix-agentic (Claude Code plugin)\n"
        "\n"
        "<!-- " + GENERATED_HEADER.replace("\n", " ") + " -->\n"
        "\n"
        "Everything in this directory is generated from `core/` and `policy/` by\n"
        "`adapters/claude/build.py`; never hand-edit it. `agents/` and `skills/`\n"
        "are absent until `core/` ships roles and skills; the build creates them\n"
        "only when there is something to put in them (ADR-0031). Install and\n"
        "verification steps are in `docs/install.md`.\n"
    )


# -----------------------------------------------------------------------------
# Ownership generation (ADR-0019)
# -----------------------------------------------------------------------------

def _generate_ownership(roles: list[dict]) -> dict:
    agents: dict[str, dict] = {}
    for role in roles:
        fm = role["frontmatter"]
        if fm.get("access") != "write":
            continue
        if not fm.get("owns"):
            continue
        agents[fm["name"]] = {
            "allow": sorted(fm["owns"]),
            "description": fm["description"][:200],
        }
    return {
        "_comment": GENERATED_HEADER,
        "_schema": {"version": 1},
        "agents": agents,
    }


# -----------------------------------------------------------------------------
# Hooks (PreToolUse guard)
# -----------------------------------------------------------------------------

# ADR-0026: Claude Code treats a hook exit code other than 0 or 2 as a
# non-blocking error and lets the tool call proceed. A missing interpreter
# (127) or an exception escaping the guard (1) must still block, so any
# non-zero exit becomes 2. Plugin hook commands run under bash on every
# platform, Git Bash on Windows (docs/install.md), so POSIX `||` is safe.
GUARD_FAILED_MESSAGE = "mendix-agentic guard could not run — run bin/doctor"
GUARD_HOOK_COMMAND = (
    'python "${CLAUDE_PLUGIN_ROOT}/policy/mxcli_guard.py"'
    f" || {{ echo '{GUARD_FAILED_MESSAGE}' >&2; exit 2; }}"
)


def _hooks_json() -> dict:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": GUARD_HOOK_COMMAND,
                        }
                    ],
                }
            ]
        }
    }


# -----------------------------------------------------------------------------
# plugin.json
# -----------------------------------------------------------------------------

def _plugin_manifest(version: str) -> dict:
    # `displayName` was rejected by `claude plugin validate` on 2.1.128 and
    # is accepted on 2.1.305 (docs/install.md), above the pinned minimum
    # (ADR-0025).
    return {
        "name": PLUGIN_NAME,
        "displayName": "Mendix Agentic",
        "version": version,
        "description": (
            "Mendix model-editing agents for mxcli, plus a PreToolUse policy "
            "guard that keeps writes safe."
        ),
        "author": {"name": "Mendix_Agentic maintainers"},
        "repository": "https://github.com/g-amess/Mendix_Agentic",
        "license": "Apache-2.0",
        "keywords": ["mendix", "mxcli", "mdl"]
    }


# -----------------------------------------------------------------------------
# Policy copy
# -----------------------------------------------------------------------------

def _copy_policy(policy_src: Path, out_root: Path) -> None:
    """Copy policy files into the plugin tree, normalising to LF (ADR-0031).

    `_write_text_lf` is used instead of `shutil.copy2` so a Windows
    checkout (where `core.autocrlf` may expand to CRLF) still produces the
    same bytes as a Linux build.
    """
    dest = out_root / "policy"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("mxcli_guard.py", "mxcli-commands.json", "stop-operations.json", "write-classes.json"):
        src = policy_src / name
        if src.exists():
            _write_text_lf(dest / name, src.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# Project settings template (deny list for downstream projects)
# -----------------------------------------------------------------------------

def _project_settings_template(commands: dict) -> dict:
    read_allow: list[str] = []
    for name, row in commands.items():
        if row.get("class") == "READ" and row.get("verified") is True:
            # Allow `mxcli <name> ...` and `mxcli <name>:...` forms
            read_allow.append(f"Bash(mxcli {name}:*)")
    read_allow.sort()
    return {
        "_comment": (
            "GENERATED template for downstream Mendix projects' .claude/settings.json. "
            "Phase 2 ships this as a template only; the bootstrap step that applies it "
            "arrives in phase 6."
        ),
        "permissions": {
            "deny": [
                "PowerShell",
                "Edit(**/*.mpr)",
                "Write(**/*.mpr)",
                "Edit(**/mprcontents/**)",
                "Write(**/mprcontents/**)"
            ],
            "allow": read_allow,
        }
    }


# -----------------------------------------------------------------------------
# Build
# -----------------------------------------------------------------------------

def _write_text_lf(path: Path, text: str) -> None:
    """Write `text` with LF line endings and no trailing BOM. Deterministic
    across OSes (ADR-0031): no CRLF leakage, no absolute paths, no
    timestamps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Use binary write to avoid Python's universal-newlines translation on
    # Windows (which would convert \n → \r\n in text mode).
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def build(core_dir: Path, policy_dir: Path, out_root: Path, version: str) -> None:
    # Fully reset the plugin dir so stale files from a previous build (or a
    # removed role) do not linger. ADR-0031: the committed tree must equal
    # a fresh build, byte for byte, with no empty directories.
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    # .claude-plugin/plugin.json
    _write_text_lf(
        out_root / ".claude-plugin" / "plugin.json",
        json.dumps(_plugin_manifest(version), indent=2) + "\n",
    )
    _write_text_lf(out_root / "README.md", _plugin_readme())

    # Agents — only materialise the directory if at least one role exists
    # (ADR-0031: no empty directories).
    roles = _load_roles(core_dir)
    cap_map = _load_capability_map()
    roles_by_name = {r["frontmatter"]["name"]: r for r in roles}
    for role in roles:
        name, md = _role_to_subagent(role, roles_by_name, cap_map)
        _write_text_lf(out_root / "agents" / f"{name}.md", md)

    # Skills — same: only materialise when a skill exists.
    skills = _load_skills(core_dir)
    for s in skills:
        _write_skill(s, out_root)

    # Hooks — always emitted; the guard is the plugin's point.
    _write_text_lf(
        out_root / "hooks" / "hooks.json",
        json.dumps(_hooks_json(), indent=2) + "\n",
    )

    # Policy copy
    _copy_policy(policy_dir, out_root)

    # ownership.json (generated) — both the plugin copy and the main
    # repo's policy/ownership.json, per ADR-0019.
    ownership = _generate_ownership(roles)
    ownership_text = json.dumps(ownership, indent=2) + "\n"
    _write_text_lf(out_root / "policy" / "ownership.json", ownership_text)
    _write_text_lf(policy_dir / "ownership.json", ownership_text)

    # Project-settings template (also committed, outside plugin dir)
    commands = _load_json(policy_dir / "mxcli-commands.json").get("commands", {})
    _write_text_lf(
        PROJECT_SETTINGS_OUT,
        json.dumps(_project_settings_template(commands), indent=2) + "\n",
    )


# -----------------------------------------------------------------------------
# --check (diff against committed output)
# -----------------------------------------------------------------------------

def _list_files(root: Path) -> set[str]:
    """Return every FILE's path relative to `root`, as forward-slash strings."""
    out: set[str] = set()
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            out.add(p.relative_to(root).as_posix())
    return out


def _read_bytes_lf(path: Path) -> bytes:
    """Read a file as bytes, normalising CRLF→LF (ADR-0031)."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _dir_diff(a: Path, b: Path) -> list[str]:
    """File-only comparison (ADR-0031). Returns relative paths that differ
    or are missing. Directories themselves are ignored — git cannot track
    empty directories, and the build must not depend on them."""
    diffs: list[str] = []
    a_files = _list_files(a)
    b_files = _list_files(b)
    for rel in sorted(a_files - b_files):
        diffs.append(f"{rel} (only in generated)")
    for rel in sorted(b_files - a_files):
        diffs.append(f"{rel} (only in committed)")
    for rel in sorted(a_files & b_files):
        if _read_bytes_lf(a / rel) != _read_bytes_lf(b / rel):
            diffs.append(f"{rel} (contents differ)")
    return diffs


def check(core_dir: Path, policy_dir: Path, committed_out: Path, version: str) -> int:
    import tempfile
    # Snapshot main repo files that build() rewrites, so --check does not
    # mutate the working tree.
    snapshot = {}
    for p in (policy_dir / "ownership.json", PROJECT_SETTINGS_OUT):
        if p.exists():
            snapshot[p] = p.read_text(encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / PLUGIN_NAME
            build(core_dir, policy_dir, tmp, version)
            if not committed_out.exists():
                print(
                    f"ERROR: committed plugin dir {committed_out} does not exist. "
                    "Run `python adapters/claude/build.py` and commit the result.",
                    file=sys.stderr,
                )
                return 1
            diffs = _dir_diff(tmp, committed_out)
            # Check main policy/ownership.json against snapshot (it was
            # rewritten by build()).
            new_ownership = (policy_dir / "ownership.json").read_text(encoding="utf-8")
            old_ownership = snapshot.get(policy_dir / "ownership.json")
            if old_ownership is not None and new_ownership != old_ownership:
                diffs.append("policy/ownership.json (regenerated contents differ)")
    finally:
        # Restore snapshot
        for p, content in snapshot.items():
            p.write_text(content, encoding="utf-8")
        # Also check PROJECT_SETTINGS_OUT separately
        old_ps = snapshot.get(PROJECT_SETTINGS_OUT)
        if PROJECT_SETTINGS_OUT.exists():
            generated_ps = PROJECT_SETTINGS_OUT.read_text(encoding="utf-8")
            if old_ps is None:
                diffs.append("adapters/claude/out/project-settings.json (new output; commit required)")
            elif old_ps != generated_ps:
                diffs.append("adapters/claude/out/project-settings.json (contents differ)")
        else:
            diffs.append("adapters/claude/out/project-settings.json (missing)")
        if diffs:
            print("ERROR: generated plugin output drifts from committed:", file=sys.stderr)
            for d in diffs:
                print(f"  - {d}", file=sys.stderr)
            print("\nRun `python adapters/claude/build.py` and commit.", file=sys.stderr)
            return 1
    print("OK: generated plugin output matches committed.")
    return 0


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=str(REPO_ROOT / "core"))
    ap.add_argument("--policy", default=str(REPO_ROOT / "policy"))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check", action="store_true", help="diff against committed output")
    args = ap.parse_args(argv)
    core = Path(args.core)
    policy = Path(args.policy)
    out = Path(args.out)
    version = _load_version(REPO_ROOT)
    if args.check:
        return check(core, policy, out, version)
    build(core, policy, out, version)
    print(f"OK: built {PLUGIN_NAME} v{version} into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
