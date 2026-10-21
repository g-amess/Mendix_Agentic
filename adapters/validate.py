#!/usr/bin/env python3
"""adapters/validate.py — validate core/ role cards and skills.

Fails with file:line messages when any of the rules in `AGENTS.md` and
`core/README.md` are violated. Stdlib only (ADR-0006).

Usage:
    python adapters/validate.py              # validate core/ and policy/
    python adapters/validate.py --core PATH  # validate a different core dir
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from adapters.lib.frontmatter import parse_frontmatter, FrontmatterError  # noqa: E402


# -----------------------------------------------------------------------------
# Role card rules
# -----------------------------------------------------------------------------

_ROLE_REQUIRED_KEYS = {
    "name", "description", "kind", "access", "owns", "capabilities",
    "model_tier", "skills", "delegates_to", "outputs",
}
_ROLE_KIND_VALUES = {"hub", "spoke"}
_ROLE_ACCESS_VALUES = {"read", "write"}
_ROLE_MODEL_TIER_VALUES = {"fast", "standard", "deep"}
_ROLE_REQUIRED_SECTIONS = ("Purpose", "Inputs", "Procedure", "Outputs", "Stop conditions")
_KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_SKILL_ALLOWED_KEYS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
}
_SKILL_REQUIRED_KEYS = {"name", "description"}
# adapter.claude.json keys and their types; emitted top-level (ADR-0027).
_SKILL_CLAUDE_SIDECAR_TYPES = {
    "disable-model-invocation": bool,
    "user-invocable": bool,
    "allowed-tools": list,
    "context": str,
    "agent": str,
    "paths": list,
}
_SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Issue:
    file: str
    line: int | None
    message: str

    def __str__(self) -> str:
        where = f"{self.file}:{self.line}" if self.line else self.file
        return f"{where}: {self.message}"


class Validator:
    def __init__(self, core_dir: Path, policy_dir: Path):
        self.core_dir = core_dir
        self.policy_dir = policy_dir
        self.issues: list[Issue] = []
        self.capabilities: dict[str, dict] = {}
        self.write_classes: dict[str, dict] = {}
        self.roles: dict[str, dict] = {}  # name → {"frontmatter": ..., "file": ...}
        self.skills: dict[str, dict] = {}  # name → {"frontmatter": ..., "file": ...}

    # -------------------------------------------------------------------------
    def err(self, file: Path | str, line: int | None, msg: str) -> None:
        self.issues.append(Issue(str(file), line, msg))

    # -------------------------------------------------------------------------
    def load_registries(self) -> None:
        caps_path = self.core_dir / "capabilities.json"
        if not caps_path.exists():
            self.err(caps_path, None, "capability registry missing")
            return
        try:
            caps = json.loads(caps_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.err(caps_path, e.lineno, f"invalid JSON: {e.msg}")
            return
        self.capabilities = caps.get("capabilities", {})

        wc_path = self.policy_dir / "write-classes.json"
        if not wc_path.exists():
            self.err(wc_path, None, "write-classes.json missing")
            return
        try:
            wc = json.loads(wc_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.err(wc_path, e.lineno, f"invalid JSON: {e.msg}")
            return
        self.write_classes = wc.get("write_classes", {})

    # -------------------------------------------------------------------------
    def validate_role(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        try:
            parsed = parse_frontmatter(text, filename=str(path))
        except FrontmatterError as e:
            self.err(e.file, e.line, e.message)
            return
        fm = parsed.data
        expected_name = path.stem

        # Required keys
        missing = _ROLE_REQUIRED_KEYS - set(fm.keys())
        if missing:
            self.err(path, 1, f"role missing required frontmatter keys: {sorted(missing)}")
            return
        unknown = set(fm.keys()) - _ROLE_REQUIRED_KEYS
        if unknown:
            self.err(path, 1, f"role has unknown frontmatter keys: {sorted(unknown)}")
            return

        # Types + values
        name = fm["name"]
        if not isinstance(name, str) or not _KEBAB_RE.match(name):
            self.err(path, 1, f"name must be kebab-case; got {name!r}")
        if name != expected_name:
            self.err(path, 1, f"name {name!r} must match filename stem {expected_name!r}")
        if name in self.roles:
            self.err(path, 1, f"duplicate role name {name!r} (also in {self.roles[name]['file']})")
            return
        desc = fm["description"]
        if not isinstance(desc, str):
            self.err(path, 1, "description must be a string")
        elif len(desc) > 400:
            self.err(path, 1, f"description is {len(desc)} chars; max 400")
        kind = fm["kind"]
        if kind not in _ROLE_KIND_VALUES:
            self.err(path, 1, f"kind must be one of {sorted(_ROLE_KIND_VALUES)}; got {kind!r}")
        access = fm["access"]
        if access not in _ROLE_ACCESS_VALUES:
            self.err(path, 1, f"access must be one of {sorted(_ROLE_ACCESS_VALUES)}; got {access!r}")
        tier = fm["model_tier"]
        if tier not in _ROLE_MODEL_TIER_VALUES:
            self.err(path, 1, f"model_tier must be one of {sorted(_ROLE_MODEL_TIER_VALUES)}; got {tier!r}")

        if not isinstance(fm["owns"], list):
            self.err(path, 1, "owns must be a list")
            return
        if not isinstance(fm["capabilities"], list):
            self.err(path, 1, "capabilities must be a list")
            return
        if not isinstance(fm["skills"], list):
            self.err(path, 1, "skills must be a list")
            return
        if not isinstance(fm["delegates_to"], list):
            self.err(path, 1, "delegates_to must be a list")
            return
        if not isinstance(fm["outputs"], list):
            self.err(path, 1, "outputs must be a list")
            return

        # Capability existence
        caps = fm["capabilities"]
        for cap in caps:
            if cap not in self.capabilities:
                self.err(path, 1, f"capability {cap!r} not in core/capabilities.json")

        # Hub/spoke rules
        if kind == "spoke":
            if fm["delegates_to"]:
                self.err(path, 1, "spoke roles must have delegates_to: []")
            if "ask-human" in caps:
                self.err(path, 1, "spoke roles may not have capability 'ask-human'")

        # Read/write rules
        if access == "read":
            if fm["owns"]:
                self.err(path, 1, "access: read roles must have owns: []")
            if "mxcli-write" in caps:
                self.err(path, 1, "access: read roles must not have capability 'mxcli-write'")
            # edit-artefacts explicitly allowed for read roles (read roles write reports).
        else:  # write
            if not fm["owns"]:
                self.err(path, 1, "access: write roles must list at least one write class in owns")
            for cls in fm["owns"]:
                if cls not in self.write_classes:
                    self.err(path, 1, f"write class {cls!r} not in policy/write-classes.json")

        # Body section check
        body = "\n".join(text.splitlines()[parsed.body_start_line - 1 :])
        for section in _ROLE_REQUIRED_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(section)}\s*$", body, re.MULTILINE):
                self.err(path, 1, f"body is missing required section `## {section}`")

        self.roles[name] = {"frontmatter": fm, "file": str(path)}

    # -------------------------------------------------------------------------
    def cross_check_roles(self) -> None:
        # delegates_to must reference existing spokes
        for name, info in self.roles.items():
            fm = info["frontmatter"]
            for target in fm.get("delegates_to", []):
                if target not in self.roles:
                    self.err(info["file"], 1, f"delegates_to references unknown role {target!r}")
                    continue
                if self.roles[target]["frontmatter"]["kind"] != "spoke":
                    self.err(
                        info["file"], 1,
                        f"delegates_to {target!r} is not a spoke (hubs delegate to spokes)"
                    )

        # skills on a role must exist
        for name, info in self.roles.items():
            fm = info["frontmatter"]
            for skill in fm.get("skills", []):
                if skill not in self.skills:
                    self.err(
                        info["file"], 1,
                        f"skill {skill!r} does not exist under core/skills/"
                    )

        # at most one write role per write class (ADR-0004)
        owners: dict[str, list[str]] = {}
        for name, info in self.roles.items():
            for cls in info["frontmatter"].get("owns", []):
                owners.setdefault(cls, []).append(name)
        for cls, names in owners.items():
            if len(names) > 1:
                self.err(
                    "policy/write-classes.json", None,
                    f"write class {cls!r} is owned by multiple roles: {sorted(names)}"
                )

    # -------------------------------------------------------------------------
    def validate_skill(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        try:
            parsed = parse_frontmatter(text, filename=str(path))
        except FrontmatterError as e:
            self.err(e.file, e.line, e.message)
            return
        fm = parsed.data

        missing = _SKILL_REQUIRED_KEYS - set(fm.keys())
        if missing:
            self.err(path, 1, f"skill missing required frontmatter keys: {sorted(missing)}")
            return
        unknown = set(fm.keys()) - _SKILL_ALLOWED_KEYS
        if unknown:
            self.err(path, 1, f"skill has non-spec frontmatter keys: {sorted(unknown)}")
            return

        name = fm["name"]
        if not isinstance(name, str) or not _SKILL_NAME_RE.match(name) or len(name) > 64:
            self.err(path, 1, f"skill name must be kebab-case ≤64 chars; got {name!r}")
            return
        parent = path.parent.name
        if parent != name:
            self.err(path, 1, f"skill name {name!r} must match parent directory {parent!r}")
            return
        if name in self.skills:
            self.err(path, 1, f"duplicate skill name {name!r} (also in {self.skills[name]['file']})")
            return

        desc = fm["description"]
        if not isinstance(desc, str) or not (1 <= len(desc) <= 1024):
            self.err(path, 1, "skill description must be 1–1024 chars")

        self.validate_claude_sidecar(path.parent / "adapter.claude.json", fm)
        self.skills[name] = {"frontmatter": fm, "file": str(path)}

    def validate_claude_sidecar(self, sidecar: Path, fm: dict) -> None:
        if not sidecar.exists():
            return
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.err(sidecar, e.lineno, f"invalid JSON: {e.msg}")
            return
        if not isinstance(data, dict):
            self.err(sidecar, None, "adapter.claude.json must be a JSON object")
            return
        for key, value in data.items():
            expected = _SKILL_CLAUDE_SIDECAR_TYPES.get(key)
            if expected is None:
                self.err(sidecar, None, f"unknown key {key!r}; allowed: {sorted(_SKILL_CLAUDE_SIDECAR_TYPES)}")
            elif not isinstance(value, expected) or (
                expected is list and not all(isinstance(x, str) for x in value)
            ):
                self.err(sidecar, None, f"{key!r} must be a {expected.__name__}")
            elif key in fm:
                self.err(sidecar, None, f"{key!r} is also set in SKILL.md; keep it in one place")
        if "context" in data and data["context"] != "fork":
            self.err(sidecar, None, "'context' must be \"fork\"")

    # -------------------------------------------------------------------------
    def run(self) -> int:
        self.load_registries()
        skills_dir = self.core_dir / "skills"
        if skills_dir.exists():
            for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
                self.validate_skill(skill_md)
        roles_dir = self.core_dir / "roles"
        if roles_dir.exists():
            for role_md in sorted(roles_dir.glob("*.md")):
                if role_md.name == "README.md":
                    continue
                self.validate_role(role_md)
        self.cross_check_roles()

        for issue in self.issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        if self.issues:
            print(f"\n{len(self.issues)} validation error(s)", file=sys.stderr)
            return 1
        print(f"OK: {len(self.roles)} role(s), {len(self.skills)} skill(s) validated.")
        return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=str(REPO_ROOT / "core"))
    ap.add_argument("--policy", default=str(REPO_ROOT / "policy"))
    args = ap.parse_args(argv)
    v = Validator(core_dir=Path(args.core), policy_dir=Path(args.policy))
    return v.run()


if __name__ == "__main__":
    raise SystemExit(main())
