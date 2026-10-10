"""Read STEP Part 21 DATA entity labels for supervision (NOT a B-rep importer).

Supports #123 = CARTESIAN_POINT(...) and #124 = VERTEX_POINT('',#123).
IDs refer only to the exact source STEP file, not stable topological names.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, Any

from .core import RuleError

_ENTITY_START = re.compile(r"^#(\d+)\s*=\s*([A-Za-z][A-Za-z_0-9]*)\s*\(", re.I | re.S)
_VERTEX_BODY = re.compile(
    r"^#\d+\s*=\s*VERTEX_POINT\s*\(\s*'(?:''|[^'])*'\s*,\s*#(\d+)\s*\)\s*;\s*$",
    re.I | re.S,
)
SUPPORTED_POINT_TYPES = frozenset(("CARTESIAN_POINT", "VERTEX_POINT"))

def _statements(path: Path) -> Iterator[str]:
    """Lex STEP statements, handling multiline DATA, strings and block comments.

    Uses a streaming reader instead of loading the complete STEP into memory.
    This is a simple entity-label validator, NOT a complete ISO 10303-21 parser.
    """
    pieces: list[str] = []
    quoted = False
    commented = False
    prev_comment_star = False
    last_slash = False
    with path.open("r", encoding="latin-1") as source:
        while True:
            chunk = source.read(65536)
            if not chunk:
                break
            for ch in chunk:
                if commented:
                    if prev_comment_star and ch == "/":
                        commented = False
                        prev_comment_star = False
                    else:
                        prev_comment_star = (ch == "*")
                    continue
                if quoted:
                    pieces.append(ch)
                    if ch == "'":
                        quoted = False  # doubled single quote re-enters quote next character
                    continue
                if ch == "*" and last_slash:
                    # Remove the slash already appended by previous iteration.
                    pieces.pop()
                    last_slash = False
                    commented = True
                    prev_comment_star = False
                    continue
                last_slash = (ch == "/")
                if ch == "'":
                    quoted = True
                if ch == ";":
                    statement = "".join(pieces).strip() + ";"
                    pieces.clear()
                    last_slash = False
                    yield statement
                else:
                    pieces.append(ch)
    if commented or quoted:
        raise RuleError(f"Unterminated string/comment in STEP file: {path}")
    if "".join(pieces).strip():
        raise RuleError(f"Unterminated STEP statement in file: {path}")


def _data_entities(path: Path) -> Iterator[tuple[int, str, str]]:
    inside_data = False
    seen_data = False
    for stmt in _statements(path):
        stripped = stmt.strip()
        command = stripped[:-1].strip().upper()
        if command == "DATA":
            inside_data = True
            seen_data = True
            continue
        if command == "ENDSEC":
            inside_data = False
            continue
        if not inside_data:
            continue
        match = _ENTITY_START.match(stripped)
        if match is not None:
            yield int(match.group(1)), match.group(2).upper(), stripped
        elif stripped.startswith("#"):
            raise RuleError(f"Malformed STEP entity in {path}: {stripped[:100]}")
    if not seen_data:
        raise RuleError(f"No DATA section found in STEP: {path}")


def resolve_step_entity(path: str | Path, entity_id: int) -> dict[str, Any]:
    """Check actual STEP entity ID and direct vertex-point reference.

    Does not transform units/occurrences nor map to a TopoDS_Vertex.
    """
    step = Path(path)
    found: tuple[str, str] | None = None
    vertex_refs: list[int] = []
    for ident, entity_type, stmt in _data_entities(step):
        if ident == entity_id:
            if found is not None:
                raise RuleError(f"Duplicate #{entity_id} STEP entity in {step}")
            found = (entity_type, stmt)
        if entity_type == "VERTEX_POINT":
            m = _VERTEX_BODY.match(stmt)
            if m and int(m.group(1)) == entity_id:
                vertex_refs.append(ident)
    if found is None:
        raise RuleError(f"STEP entity #{entity_id} does not exist in: {step}")
    entity_type, stmt = found
    if entity_type not in SUPPORTED_POINT_TYPES:
        raise RuleError(
            f"#{entity_id} is {entity_type}, not a point entity "
            "(expected CARTESIAN_POINT or VERTEX_POINT)"
        )
    result: dict[str, Any] = {
        "entity_id": entity_id, "entity_label": f"#{entity_id}",
        "entity_type": entity_type,
        "geometry_point_entity_id": entity_id if entity_type == "CARTESIAN_POINT" else None,
        "linked_vertex_point_entity_ids": sorted(vertex_refs) if entity_type == "CARTESIAN_POINT" else [],
        "topods_vertex_verified": False,
    }
    if entity_type == "VERTEX_POINT":
        ref = _VERTEX_BODY.match(stmt)
        if not ref:
            raise RuleError(f"#{entity_id} is a VERTEX_POINT but its point reference cannot be parsed")
        target_id = int(ref.group(1))
        geom: str | None = None
        for ident, typ, _ in _data_entities(step):
            if ident == target_id:
                if geom is not None:
                    raise RuleError(f"Duplicate referred-to STEP entity #{target_id}")
                geom = typ
        if geom is None:
            raise RuleError(f"#{entity_id} references nonexistent geometry #{target_id}")
        if geom != "CARTESIAN_POINT":
            raise RuleError(f"#{entity_id} refers to #{target_id} ({geom}); expected CARTESIAN_POINT")
        result["geometry_point_entity_id"] = target_id
    return result
