"""Training STEP paths and entity-ID labels, independent of STEP B-rep import."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import RuleError
from .step_entities import resolve_step_entity

DEFAULT_MANIFEST = Path("data/training/labels.json")
VARIANTS = ("a", "b", "c")


def parse_entity_id(value: Any) -> int:
    """Accept 118 or '#118'; reject booleans, coordinates and other values."""
    if type(value) is int and value > 0:
        return value
    if isinstance(value, str) and value.startswith("#") and value[1:].isdigit():
        num = int(value[1:])
        if num > 0:
            return num
    raise RuleError('target_point.entity_id must be a positive integer, or a string like "#118"')


def validate_step_inputs(manifest_path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Validate three STEP files, entity labels and linked CARTESIAN_POINT references.

    This reads STEP DATA entity statements, but does NOT translate CAD B-rep,
    inspect assembly instances, or verify correspondence to TopoDS_Vertex.
    """
    path = Path(manifest_path).expanduser()
    if not path.is_file():
        raise RuleError(
            f"Labels JSON not found: {path}. Copy data/training/labels.example.json "
            "to data/training/labels.json and enter the target STEP entity_id for each type."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleError(f"Cannot read labels JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise RuleError("Expected labels JSON object with schema_version: 2 (STEP entity IDs)")
    cases = data.get("training_cases")
    if not isinstance(cases, list) or len(cases) != 3:
        raise RuleError("training_cases must contain exactly 3 variants (a,b,c)")
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    root = path.resolve().parent
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise RuleError(f"training_cases[{index}] must be an object")
        variant = case.get("variant")
        if type(variant) is not str or variant not in VARIANTS or variant in seen:
            raise RuleError(f"Invalid or duplicate variant {variant!r}; expected a,b,c")
        seen.add(variant)
        step_name = case.get("step_file")
        expected = f"type_{variant}.step"
        if step_name != expected:
            raise RuleError(f"variant {variant}: step_file must be exactly {expected!r}")
        target = case.get("target_point")
        if not isinstance(target, dict) or "entity_id" not in target:
            raise RuleError(f"variant {variant}: specify target_point.entity_id")
        if "xyz_mm" in target or "point_kind" in target:
            raise RuleError("Coordinates/point_kind are obsolete; use entity_id with schema_version 2")
        entity_id = parse_entity_id(target["entity_id"])
        step_path = root / expected
        if not step_path.is_file():
            raise RuleError(f"variant {variant}: STEP file missing: {step_path}")
        if step_path.stat().st_size == 0:
            raise RuleError(f"variant {variant}: STEP file is empty: {step_path}")
        resolved = resolve_step_entity(step_path, entity_id)
        checked.append({
            "variant": variant,
            "step_file": str(step_path),
            "file_size_bytes": step_path.stat().st_size,
            **resolved,
        })
    if seen != set(VARIANTS):
        raise RuleError("training_cases must include all variants a, b and c")
    return {
        "status": "step_entity_labels_valid",
        "schema_version": 2,
        "manifest": str(path),
        "cases": checked,
        "step_entity_ids_verified": True,
        "step_geometry_verified": False,
        "rule_discovery_ready": False,
        "next_milestone": "Bind labels by STEP reader entity -> OCCT geometry/topology and synthesize common rule",
    }
