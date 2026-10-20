"""Restricted YAML-subset frontmatter parser (ADR-0021).

Supports exactly:

- `key: value` scalars (plain, 'single', or "double"-quoted strings;
  booleans `true`/`false`; integers).
- Block lists:
      key:
        - item1
        - item2
- Flow lists: `key: [a, b, "c with spaces"]`.
- ONE level of nested mapping with scalar values (needed for the Agent
  Skills `metadata` field — see agentskills.io/specification):
      metadata:
        author: example-org
        version: "1.0"

Anything else — deeper nesting, multi-line strings (`|`, `>`), anchors,
tags, dates, floats, nulls, flow mappings `{a: b}` — raises
`FrontmatterError` with the file:line that triggered the failure.

The frontmatter block is delimited by `---` on its own line at the top of
the file and a closing `---` on its own line. The two delimiters, and
every blank line between them, count towards the line numbers reported
in error messages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class FrontmatterError(Exception):
    """Raised when the frontmatter cannot be parsed under the restricted rules."""

    def __init__(self, message: str, *, file: str, line: int) -> None:
        super().__init__(f"{file}:{line}: {message}")
        self.file = file
        self.line = line
        self.message = message


@dataclass
class ParsedFrontmatter:
    data: dict[str, Any]
    body_start_line: int  # 1-based line number of the first body line


_SCALAR_TRUE = {"true", "True", "TRUE"}
_SCALAR_FALSE = {"false", "False", "FALSE"}
_INT_RE = re.compile(r"^-?\d+$")
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")


def _parse_scalar(raw: str, *, file: str, line: int) -> Any:
    s = raw.strip()
    if not s:
        raise FrontmatterError("empty scalar value", file=file, line=line)
    if s in _SCALAR_TRUE:
        return True
    if s in _SCALAR_FALSE:
        return False
    if _INT_RE.match(s):
        return int(s)
    # Quoted strings. Double quotes support \" and \\; single quotes are literal.
    if s.startswith('"') and s.endswith('"'):
        inner = s[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    if s.startswith("'") and s.endswith("'"):
        inner = s[1:-1]
        if "\\" in inner:
            raise FrontmatterError(
                "backslash in single-quoted string (use double quotes)",
                file=file, line=line,
            )
        return inner
    # Reject constructs this parser does not support
    if s.startswith("{"):
        raise FrontmatterError(
            "flow mapping `{...}` not supported — use block form or JSON sidecar",
            file=file, line=line,
        )
    if s in {"~", "null", "Null", "NULL"}:
        raise FrontmatterError(
            "null values are not supported — omit the key instead", file=file, line=line
        )
    if s.startswith("|") or s.startswith(">"):
        raise FrontmatterError(
            "multi-line strings (|, >) are not supported", file=file, line=line
        )
    if s.startswith("&") or s.startswith("*") or s.startswith("!"):
        raise FrontmatterError(
            "YAML anchors/tags are not supported", file=file, line=line
        )
    if re.fullmatch(r"-?\d+\.\d+", s):
        raise FrontmatterError(
            "floats are not supported — use string or integer", file=file, line=line
        )
    # Plain scalar: unquoted string. Reject if it contains a colon-space
    # (ambiguous with a nested mapping).
    if re.search(r":\s", s):
        raise FrontmatterError(
            "unquoted scalar contains a colon-space (looks like a nested mapping) — "
            "quote the string",
            file=file, line=line,
        )
    return s


def _parse_flow_list(raw: str, *, file: str, line: int) -> list[Any]:
    """Parse `[a, b, "c, d"]`-style single-line lists."""
    inner = raw.strip()
    if not (inner.startswith("[") and inner.endswith("]")):
        raise FrontmatterError("flow list missing [ or ]", file=file, line=line)
    body = inner[1:-1].strip()
    if not body:
        return []
    # Split on commas, respecting quotes.
    out: list[Any] = []
    buf: list[str] = []
    in_single = False
    in_double = False
    for ch in body:
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
        elif ch == "," and not in_single and not in_double:
            out.append(_parse_scalar("".join(buf), file=file, line=line))
            buf = []
        else:
            buf.append(ch)
    if in_single or in_double:
        raise FrontmatterError("unterminated quote in flow list", file=file, line=line)
    if buf:
        out.append(_parse_scalar("".join(buf), file=file, line=line))
    return out


def _is_block_list_item(line: str) -> bool:
    stripped = line.lstrip(" ")
    return stripped.startswith("- ") or stripped == "-"


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_frontmatter(text: str, *, filename: str = "<string>") -> ParsedFrontmatter:
    """Parse the frontmatter at the top of `text`.

    Raises FrontmatterError (with file:line) if the restricted rules are
    violated. If the text has no leading `---`, returns ParsedFrontmatter
    with empty data and body_start_line = 1.
    """
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return ParsedFrontmatter(data={}, body_start_line=1)

    # Find the closing `---`
    close_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            close_idx = i
            break
    if close_idx is None:
        raise FrontmatterError(
            "frontmatter opened with `---` but no closing `---` found",
            file=filename, line=1,
        )

    data: dict[str, Any] = {}
    i = 1
    while i < close_idx:
        raw = lines[i]
        line_no = i + 1  # 1-based for error messages
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        indent = _indent_of(raw)
        if indent != 0:
            raise FrontmatterError(
                f"unexpected indentation (keys must start at column 0)",
                file=filename, line=line_no,
            )
        if ":" not in raw:
            raise FrontmatterError(
                "line is not a `key: value` pair and not a comment",
                file=filename, line=line_no,
            )
        key, _, rest = raw.partition(":")
        key = key.strip()
        if not _IDENT_RE.match(key):
            raise FrontmatterError(
                f"invalid key {key!r} (must match [A-Za-z_][A-Za-z0-9_-]*)",
                file=filename, line=line_no,
            )
        if key in data:
            raise FrontmatterError(f"duplicate key {key!r}", file=filename, line=line_no)
        rest = rest.strip()
        if not rest:
            # Could be a block list OR a block mapping. Peek the first
            # non-blank/non-comment indented line to decide.
            peek = i + 1
            while peek < close_idx:
                sub = lines[peek]
                if sub.strip() and not sub.lstrip().startswith("#"):
                    break
                peek += 1
            if peek >= close_idx or _indent_of(lines[peek]) == 0:
                # Empty block → empty list by convention
                data[key] = []
                i += 1
                continue
            if _is_block_list_item(lines[peek]):
                items: list[Any] = []
                i += 1
                while i < close_idx:
                    sub = lines[i]
                    sub_line = i + 1
                    if not sub.strip() or sub.lstrip().startswith("#"):
                        i += 1
                        continue
                    if _indent_of(sub) == 0:
                        break
                    if not _is_block_list_item(sub):
                        raise FrontmatterError(
                            f"expected `- item` under {key!r}, got: {sub.rstrip()!r}",
                            file=filename, line=sub_line,
                        )
                    item_text = sub.lstrip(" ")[1:].strip()
                    if not item_text:
                        raise FrontmatterError(
                            "empty list item", file=filename, line=sub_line
                        )
                    items.append(_parse_scalar(item_text, file=filename, line=sub_line))
                    i += 1
                data[key] = items
                continue
            # Block mapping: `key:` followed by indented `subkey: scalar`
            # lines. One level only.
            mapping: dict[str, Any] = {}
            i += 1
            while i < close_idx:
                sub = lines[i]
                sub_line = i + 1
                if not sub.strip() or sub.lstrip().startswith("#"):
                    i += 1
                    continue
                if _indent_of(sub) == 0:
                    break
                if ":" not in sub:
                    raise FrontmatterError(
                        f"expected `subkey: value` under {key!r}, got: {sub.rstrip()!r}",
                        file=filename, line=sub_line,
                    )
                subkey, _, subval = sub.partition(":")
                subkey = subkey.strip()
                if not _IDENT_RE.match(subkey):
                    raise FrontmatterError(
                        f"invalid nested key {subkey!r} under {key!r}",
                        file=filename, line=sub_line,
                    )
                subval = subval.strip()
                if not subval:
                    raise FrontmatterError(
                        f"nested mapping under {key!r} requires scalar values "
                        "(no deeper nesting supported)",
                        file=filename, line=sub_line,
                    )
                mapping[subkey] = _parse_scalar(subval, file=filename, line=sub_line)
                i += 1
            data[key] = mapping
            continue
        if rest.startswith("["):
            data[key] = _parse_flow_list(rest, file=filename, line=line_no)
        else:
            data[key] = _parse_scalar(rest, file=filename, line=line_no)
        i += 1

    body_start = close_idx + 2  # line after the closing `---` (1-based)
    return ParsedFrontmatter(data=data, body_start_line=body_start)
