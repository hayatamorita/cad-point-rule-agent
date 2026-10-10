"""Validate file placement/JSON labels for future STEP-based training.

This is NOT a STEP geometry importer and cannot verify a real CAD vertex.
"""
from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any

from .core import RuleError

DEFAULT_MANIFEST = Path('data/training/labels.json')
VARIANTS = ('a', 'b', 'c')


def validate_step_inputs(manifest_path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Validate the 3 STEP filenames and coordinate-label schema.

    Returns metadata only, not STEP content. Paths are relative to the JSON.
    """
    path = Path(manifest_path).expanduser()
    if not path.is_file():
        raise RuleError(
            f'Labels JSON not found: {path}. Copy data/training/labels.example.json '
            'to data/training/labels.json and fill in each xyz_mm.'
        )
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleError(f'Cannot read labels JSON: {exc}') from exc
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise RuleError('Expected JSON object with schema_version: 1')
    if data.get('units') != 'mm':
        raise RuleError('Only millimetres (units: "mm") are supported by this contract')
    if data.get('coordinate_frame') != 'step_global':
        raise RuleError('coordinate_frame must be "step_global" (assembly root/world frame)')
    cases = data.get('training_cases')
    if not isinstance(cases, list) or len(cases) != 3:
        raise RuleError('training_cases must contain exactly A, B, C')
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    root = path.resolve().parent
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise RuleError(f'training_cases[{index}] must be an object')
        variant = case.get('variant')
        if variant not in VARIANTS or variant in seen:
            raise RuleError(f'Invalid or duplicate variant {variant!r}; require a,b,c')
        seen.add(variant)
        step_name = case.get('step_file')
        expected = f'type_{variant}.step'
        if step_name != expected:
            raise RuleError(f'variant {variant}: step_file must be exactly {expected!r}')
        target = case.get('target_point')
        if not isinstance(target, dict) or target.get('point_kind') != 'vertex':
            raise RuleError(f'variant {variant}: target_point.point_kind must be "vertex"')
        xyz = target.get('xyz_mm')
        if not isinstance(xyz, list) or len(xyz) != 3 or any(
            type(v) not in (int, float) or not isfinite(float(v)) for v in xyz
        ):
            raise RuleError(f'variant {variant}: fill xyz_mm with three finite numbers')
        tolerance = target.get('tolerance_mm')
        if type(tolerance) not in (int, float) or not isfinite(float(tolerance)) or tolerance <= 0:
            raise RuleError(f'variant {variant}: tolerance_mm must be positive and finite')
        occurrence = target.get('occurrence_path')
        if occurrence is not None and not isinstance(occurrence, str):
            raise RuleError(f'variant {variant}: occurrence_path must be string or null')
        step_path = root / expected
        if not step_path.is_file():
            raise RuleError(f'variant {variant}: STEP file missing: {step_path}')
        if step_path.stat().st_size == 0:
            raise RuleError(f'variant {variant}: STEP file is empty: {step_path}')
        checked.append({
            'variant': variant,
            'step_file': str(step_path),
            'xyz_mm': [float(v) for v in xyz],
            'tolerance_mm': float(tolerance),
            'occurrence_path': occurrence,
            'file_size_bytes': step_path.stat().st_size,
        })
    if seen != set(VARIANTS):
        raise RuleError('training_cases must contain variants a, b and c')
    return {
        'status': 'input_files_and_labels_valid',
        'schema_version': 1,
        'manifest': str(path),
        'coordinate_frame': 'step_global',
        'cases': checked,
        'step_geometry_verified': False,
        'rule_discovery_ready': False,
        'next_milestone': 'Implement STEP importer and vertex snapping before synthesis',
    }
