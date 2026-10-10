"""Pure-Python MVP: synthesize a minimal conjunctive rule over precomputed features.

This module intentionally DOES NOT read STEP. Coordinates are used only by
supervision resolution and scoring, never by the synthesized rule.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from math import dist, isfinite
from typing import Any, Mapping

SCHEMA_VERSION = 1
ALLOWED_FEATURES = frozenset({
    "front_region", "on_closed_wire", "on_inner_closed_wire",
    "endpoint_of_line", "parallel_to_reference", "left_endpoint",
    "adjacent_to_planar_face", "on_outer_wire", "on_cylindrical_face",
    "near_frontmost_face", "on_symmetry_plane", "reference_edge_adjacent",
})

class RuleError(ValueError):
    """Invalid input, rule or invalid application."""

class AmbiguousSelectionError(RuleError):
    """A matching label/rule does not resolve to exactly one point."""

class NoRuleFoundError(RuleError):
    """No rule exists within the explored conjunction grammar."""

@dataclass(frozen=True)
class Vertex:
    key: str  # Local diagnostic identity ONLY; not a rule feature.
    xyz: tuple[float, float, float]
    features: Mapping[str, bool]

@dataclass(frozen=True)
class Model:
    model_id: str  # Diagnostic identity ONLY; not a rule feature.
    vertices: tuple[Vertex, ...]
    units: str
    coordinate_frame: str

@dataclass(frozen=True)
class Label:
    xyz: tuple[float, float, float]
    tolerance_mm: float
    coordinate_frame: str

@dataclass(frozen=True, order=True)
class Predicate:
    feature: str
    equals: bool

@dataclass(frozen=True)
class Rule:
    predicates: tuple[Predicate, ...]

def _xyz(value: Any) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise RuleError("xyz must contain exactly three numeric coordinates")
    if any(type(v) not in (int, float) or not isfinite(float(v)) for v in value):
        raise RuleError("xyz must contain only finite numeric coordinates")
    return tuple(float(v) for v in value)  # type: ignore[return-value]

def load_model(raw: Mapping[str, Any]) -> Model:
    if raw.get("units") != "mm":
        raise RuleError("MVP supports only millimetres; provide normalized units")
    frame = raw.get("coordinate_frame")
    if not isinstance(frame, str) or not frame:
        raise RuleError("coordinate_frame is required")
    model_id = raw.get("model_id", "unnamed")
    if not isinstance(model_id, str):
        raise RuleError("model_id must be text")
    vertices_raw = raw.get("vertices")
    if not isinstance(vertices_raw, list) or not vertices_raw:
        raise RuleError("vertices must be a nonempty array")
    vertices: list[Vertex] = []
    keys: set[str] = set()
    for index, entry in enumerate(vertices_raw):
        if not isinstance(entry, dict):
            raise RuleError(f"vertex[{index}] must be an object")
        key = entry.get("key")
        if not isinstance(key, str) or not key or key in keys:
            raise RuleError("each vertex requires a unique nonempty key")
        keys.add(key)
        features = entry.get("features")
        if not isinstance(features, dict):
            raise RuleError("features must be a key-to-boolean object")
        for name, value in features.items():
            if name not in ALLOWED_FEATURES or type(value) is not bool:
                raise RuleError(f"unsupported or non-boolean feature: {name}")
        vertices.append(Vertex(key=key, xyz=_xyz(entry.get("xyz")), features=dict(features)))
    return Model(model_id=model_id, vertices=tuple(vertices), units="mm", coordinate_frame=frame)

def load_label(raw: Mapping[str, Any]) -> Label:
    tolerance = raw.get("tolerance_mm")
    if type(tolerance) not in (int, float) or not isfinite(float(tolerance)) or tolerance <= 0:
        raise RuleError("label tolerance_mm must be a finite positive number")
    frame = raw.get("coordinate_frame")
    if not isinstance(frame, str) or not frame:
        raise RuleError("label coordinate_frame is required")
    return Label(xyz=_xyz(raw.get("xyz")), tolerance_mm=float(tolerance), coordinate_frame=frame)

def resolve_target(model: Model, label: Label) -> Vertex:
    if label.coordinate_frame != model.coordinate_frame:
        raise RuleError("coordinate frames differ; explicit transformation required")
    matches = [vertex for vertex in model.vertices if dist(vertex.xyz, label.xyz) <= label.tolerance_mm]
    if len(matches) != 1:
        raise AmbiguousSelectionError(
            f"label for {model.model_id}: expected one vertex within tolerance, found {len(matches)}"
        )
    return matches[0]

def _matches(vertex: Vertex, pred: Predicate) -> bool:
    # Missing means UNKNOWN rather than False.
    return pred.feature in vertex.features and vertex.features[pred.feature] is pred.equals

def select(model: Model, rule: Rule) -> tuple[Vertex, ...]:
    for pred in rule.predicates:
        if pred.feature not in ALLOWED_FEATURES or type(pred.equals) is not bool:
            raise RuleError("rule has unsupported predicate")
    return tuple(vertex for vertex in model.vertices if all(_matches(vertex, pred) for pred in rule.predicates))

def apply_unique(model: Model, rule: Rule) -> Vertex:
    matches = select(model, rule)
    if len(matches) != 1:
        raise AmbiguousSelectionError(
            f"rule selected {len(matches)} points on {model.model_id}; expected exactly 1"
        )
    return matches[0]

def make_training_cases(data: Mapping[str, Any]) -> tuple[tuple[Model, Label], ...]:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise RuleError("unsupported dataset schema_version")
    raw_cases = data.get("training_cases")
    if not isinstance(raw_cases, list) or len(raw_cases) < 3:
        raise RuleError("at least three training cases are required")
    cases: list[tuple[Model, Label]] = []
    for case in raw_cases:
        if not isinstance(case, dict) or not isinstance(case.get("model"), dict) or not isinstance(case.get("label"), dict):
            raise RuleError("each case must contain model and label objects")
        cases.append((load_model(case["model"]), load_label(case["label"])))
    return tuple(cases)

def synthesize(cases: tuple[tuple[Model, Label], ...], *, max_predicates: int = 8) -> Rule:
    """Find minimum-length common conjunction, using all non-targets as negatives.

    Exhaustive combinations suit this small whitelist only. Replace with
    ILP / branch-and-bound for a larger production DSL.
    """
    if len(cases) < 3:
        raise RuleError("at least three labeled cases required")
    if not isinstance(max_predicates, int) or max_predicates <= 0:
        raise RuleError("max_predicates must be a positive integer")
    targets = [resolve_target(model, label) for model, label in cases]
    labels_consistent = sorted([
        Predicate(feature, boolean)
        for feature in ALLOWED_FEATURES
        for boolean in (False, True)
        if all(_matches(target, Predicate(feature, boolean)) for target in targets)
    ])
    negatives = [
        candidate
        for (model, _), target in zip(cases, targets)
        for candidate in model.vertices
        if candidate.key != target.key
    ]
    if not negatives:
        raise RuleError("at least one negative candidate is required")
    for size in range(1, min(max_predicates, len(labels_consistent)) + 1):
        for combo in combinations(labels_consistent, size):
            if all(any(not _matches(negative, p) for p in combo) for negative in negatives):
                rule = Rule(predicates=combo)
                verify_training_cases(cases, rule)
                return rule
    raise NoRuleFoundError(
        "no unique shared conjunction found; expand the geometry feature grammar or sample additional variants"
    )

def verify_training_cases(cases: tuple[tuple[Model, Label], ...], rule: Rule) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for model, label in cases:
        target = resolve_target(model, label)
        selected = apply_unique(model, rule)
        delta = dist(selected.xyz, target.xyz)
        if delta > label.tolerance_mm:
            raise RuleError(f"wrong target selected on {model.model_id}: delta {delta} mm")
        report.append({"model_id": model.model_id, "selected_key": selected.key, "distance_mm": delta, "candidate_count": 1})
    return report

def rule_to_dict(rule: Rule) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_type": "conjunction_of_boolean_geometry_features",
        "predicates": [{"feature": p.feature, "equals": p.equals} for p in rule.predicates],
        "notice": "Features must be computed from input geometry WITHOUT the training label; STEP adapter is not implemented.",
    }

def rule_from_dict(value: Mapping[str, Any]) -> Rule:
    if value.get("schema_version") != SCHEMA_VERSION or value.get("rule_type") != "conjunction_of_boolean_geometry_features":
        raise RuleError("unsupported rule schema")
    preds = value.get("predicates")
    if not isinstance(preds, list) or not preds:
        raise RuleError("nonempty rule predicates required")
    parsed: list[Predicate] = []
    for pred in preds:
        if not isinstance(pred, dict) or pred.get("feature") not in ALLOWED_FEATURES or type(pred.get("equals")) is not bool:
            raise RuleError("invalid predicate in serialized rule")
        parsed.append(Predicate(pred["feature"], pred["equals"]))
    return Rule(predicates=tuple(parsed))
