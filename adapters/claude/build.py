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


def _emit_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
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
    # delegate → Agent(<spoke>, …)
    if "delegate" in fm.get("capabilities", []):
        delegates = fm.get("delegates_to", [])
        if delegates:
            agent_tool = "Agent(" + ",".join(sorted(delegates)) + ")"
            if agent_tool not in seen:
                seen.add(agent_tool)
                tools.append(agent_tool)

    model = capability_map["model_tier_to_alias"].get(fm["model_tier"], "sonnet")

    sub_fm: dict[str, Any] = {
        "name": name,
        "description": fm["description"],
        "tools": tools,
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
    extras = skill["claude_extras"]
    if extras:
        # Place Claude-only fields in `metadata.claude` to stay within the
        # Agent Skills spec (metadata is a map of str→str; we JSON-encode).
        md = merged_fm.get("metadata", {})
        if not isinstance(md, dict):
            md = {}
        md = dict(md)
        md["claude"] = json.dumps(extras, separators=(",", ":"))
        merged_fm["metadata"] = md
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
            if not value:
                lines.append(f"{key}: []")
            else:
                items = ", ".join(_emit_scalar(x) for x in value)
                lines.append(f"{key}: [{items}]")
        else:
            lines.append(f"{key}: {_emit_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


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

def _hooks_json() -> dict:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "python \"${CLAUDE_PLUGIN_ROOT}/policy/mxcli_guard.py\""
                            ),
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
    # NOTE: `displayName` is listed in the plugin-manifest reference at
    # code.claude.com/docs/en/plugins/manifest-reference but is rejected
    # by `claude plugin validate` on older Claude Code CLIs. Omitted here
    # until the installed CLI accepts it (phase 3+ check).
    return {
        "name": PLUGIN_NAME,
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
    dest = out_root / "policy"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in ("mxcli_guard.py", "mxcli-commands.json", "stop-operations.json", "write-classes.json"):
        src = policy_src / name
        if src.exists():
            shutil.copy2(src, dest / name)


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

def build(core_dir: Path, policy_dir: Path, out_root: Path, version: str) -> None:
    out_root.mkdir(parents=True, exist_ok=True)

    # .claude-plugin/plugin.json
    (out_root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (out_root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(_plugin_manifest(version), indent=2) + "\n", encoding="utf-8"
    )

    # Agents
    roles = _load_roles(core_dir)
    agents_dir = out_root / "agents"
    if agents_dir.exists():
        shutil.rmtree(agents_dir)
    agents_dir.mkdir(parents=True)
    cap_map = _load_capability_map()
    roles_by_name = {r["frontmatter"]["name"]: r for r in roles}
    for role in roles:
        name, md = _role_to_subagent(role, roles_by_name, cap_map)
        (agents_dir / f"{name}.md").write_text(md, encoding="utf-8")

    # Skills
    skills = _load_skills(core_dir)
    skills_root = out_root / "skills"
    if skills_root.exists():
        shutil.rmtree(skills_root)
    skills_root.mkdir(parents=True)
    for s in skills:
        _write_skill(s, out_root)

    # Hooks
    hooks_dir = out_root / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (hooks_dir / "hooks.json").write_text(
        json.dumps(_hooks_json(), indent=2) + "\n", encoding="utf-8"
    )

    # Policy copy
    _copy_policy(policy_dir, out_root)

    # ownership.json (generated) — both the plugin copy and the main
    # repo's policy/ownership.json, per ADR-0019.
    ownership = _generate_ownership(roles)
    (out_root / "policy" / "ownership.json").write_text(
        json.dumps(ownership, indent=2) + "\n", encoding="utf-8"
    )
    main_ownership = policy_dir / "ownership.json"
    main_ownership.write_text(
        json.dumps(ownership, indent=2) + "\n", encoding="utf-8"
    )

    # Project-settings template (also committed, outside plugin dir)
    commands = _load_json(policy_dir / "mxcli-commands.json").get("commands", {})
    PROJECT_SETTINGS_OUT.parent.mkdir(parents=True, exist_ok=True)
    PROJECT_SETTINGS_OUT.write_text(
        json.dumps(_project_settings_template(commands), indent=2) + "\n",
        encoding="utf-8",
    )


# -----------------------------------------------------------------------------
# --check (diff against committed output)
# -----------------------------------------------------------------------------

def _dir_diff(a: Path, b: Path, prefix: str = "") -> list[str]:
    """Deep comparison; returns list of relative paths that differ or are missing."""
    diffs: list[str] = []
    cmp = filecmp.dircmp(str(a), str(b))
    for name in cmp.left_only:
        diffs.append(f"{prefix}{name} (only in generated)")
    for name in cmp.right_only:
        diffs.append(f"{prefix}{name} (only in committed)")
    for name in cmp.diff_files:
        diffs.append(f"{prefix}{name} (contents differ)")
    for name in cmp.common_dirs:
        diffs.extend(_dir_diff(a / name, b / name, prefix + name + "/"))
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
