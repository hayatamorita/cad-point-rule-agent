"""Static catalog and reuse proposals for user-supplied historical pythonOCC code.

Untrusted scripts are NEVER imported or executed. Analysis uses Python's AST.
Catalog entries are candidate evidence, not certified reusable primitives.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .core import RuleError

DEFAULT_LEGACY_ROOT = Path("data/legacy_pyocc")
DEFAULT_CATALOG_PATH = Path("data/legacy_catalog/index.json")
DEFAULT_PROPOSALS_ROOT = Path("data/legacy_catalog/proposals")
MAX_FILE_BYTES = 2_000_000

# Geometry/tag keyword evidence; tags are hints, not semantic guarantees.
TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "topology": ("topexp", "topabs", "toptools", "topods", "topology", "topological"),
    "step_io": ("stepcontrol", "stepcafcontrol", "readfile", "transferroots", "step_reader"),
    "assembly": ("xcaf", "xdocument", "location", "assembly", "occurrence"),
    "solid": ("solid", "comp_solid"),
    "face": ("face", "surface", "breptool_surface"),
    "wire": ("wire", "wireexplorer"),
    "closed_loop": ("closed", "isclosed", "inner_wire", "outer_wire", "loop"),
    "edge": ("edge", "edgeexplorer", "curve", "adaptorcurve"),
    "vertex": ("vertex", "vertices", "breptool_pnt"),
    "parallel": ("parallel", "isparallel", "is_parallel", "anglewithref"),
    "perpendicular": ("perpendicular", "orthogonal", "normal_to"),
    "direction": ("direction", "vector", "gp_dir", "gp_vec", "orientation"),
    "front": ("front", "forward", "foremost", "ahead"),
    "left": ("left", "leftmost"),
    "endpoint": ("endpoint", "end_point", "startpoint", "start_point"),
    "adjacency": ("adjacent", "connect", "incident", "neighbors", "ancestors"),
    "distance": ("distance", "distanceto", "length", "gprop"),
    "intersection": ("intersect", "intersection", "intcs", "intss"),
    "reference": ("reference", "ref_edge", "baseline", "datum"),
    "point_selection": ("find_point", "select_point", "target_point", "find_vertex", "select_vertex"),
}
JP_SYNONYMS = {
    "閉ループ": "closed_loop", "閉じた": "closed_loop", "ループ": "closed_loop",
    "平行": "parallel", "直交": "perpendicular", "垂直": "perpendicular",
    "前方": "front", "前側": "front", "左側": "left",
    "辺": "edge", "エッジ": "edge", "線分": "edge",
    "頂点": "vertex", "点": "vertex", "端点": "endpoint",
    "隣接": "adjacency", "面": "face", "長さ": "distance",
    "基準": "reference", "ワイヤ": "wire", "交点": "intersection",
}
DSL_HINTS = {
    "closed_loop": ["on_closed_wire", "on_inner_closed_wire"],
    "parallel": ["parallel_to_reference"],
    "front": ["front_region", "near_frontmost_face"],
    "left": ["left_endpoint"],
    "endpoint": ["endpoint_of_line", "left_endpoint"],
    "face": ["adjacent_to_planar_face"],
    "reference": ["reference_edge_adjacent"],
    "wire": ["on_closed_wire"],
}


def _call_name(expr: ast.AST) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        parent = _call_name(expr.value)
        return f"{parent}.{expr.attr}" if parent else expr.attr
    return ""


def _tags(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        tag
        for tag, keywords in TAG_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    )


def _function_entry(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    file_path: str,
    cls: str | None,
    source_sha256: str,
) -> dict[str, Any]:
    qualname = f"{cls}.{node.name}" if cls else node.name
    calls = sorted({
        value for item in ast.walk(node)
        if isinstance(item, ast.Call)
        if (value := _call_name(item.func))
    })
    params = [
        arg.arg
        for arg in (
            node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        )
    ]
    if node.args.vararg:
        params.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        params.append("**" + node.args.kwarg.arg)
    docstring = (ast.get_docstring(node) or "").strip()[:400]
    # Local module source, function calls and docstring are analyzed but
    # only a compact, non-source-code catalog is saved.
    evidence = " ".join([qualname, docstring, *calls])
    tags = _tags(evidence)
    suggestions = sorted({hint for tag in tags for hint in DSL_HINTS.get(tag, ())})
    return {
        "function_id": f"{file_path}::{qualname}",
        "file": file_path,
        "qualname": qualname,
        "lineno": node.lineno,
        "end_lineno": node.end_lineno,
        "parameters": params,
        "docstring_excerpt": docstring,
        "called_symbols": calls[:80],
        "tags": tags,
        "potential_dsl_features": suggestions,
        "source_sha256": source_sha256,
        "reuse_status": "candidate_not_approved",
    }


def build_legacy_catalog(root: str | Path = DEFAULT_LEGACY_ROOT) -> dict[str, Any]:
    """Index files recursively without importing, evaluating or executing them."""
    folder = Path(root).expanduser()
    if not folder.is_dir():
        raise RuleError(
            f"Historical pyocc folder not found: {folder}; "
            "create it and put .py scripts under data/legacy_pyocc/"
        )
    absolute_root = folder.resolve()
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    file_count = 0
    for path in sorted(folder.rglob("*.py")):
        # Do not follow symlinks outside the approved scan root.
        if not path.is_file() or not path.resolve().is_relative_to(absolute_root):
            continue
        rel = path.relative_to(folder).as_posix()
        if path.stat().st_size > MAX_FILE_BYTES:
            failures.append({"file": rel, "reason": "file too large (>2 MB)"})
            continue
        file_count += 1
        try:
            source = path.read_bytes()
            try:
                text = source.decode("utf-8-sig")
            except UnicodeDecodeError:
                raise ValueError("not UTF-8 source")
            tree = ast.parse(text, filename=rel)
        except (OSError, ValueError, SyntaxError) as exc:
            failures.append({"file": rel, "reason": type(exc).__name__ + ": " + str(exc)[:180]})
            continue
        sha = hashlib.sha256(source).hexdigest()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entries.append(_function_entry(node, file_path=rel, cls=None, source_sha256=sha))
            elif isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        entries.append(_function_entry(child, file_path=rel, cls=node.name, source_sha256=sha))
    return {
        "schema_version": 1,
        "library_root": str(absolute_root),
        "analyzed_python_files": file_count,
        "function_count": len(entries),
        "functions": entries,
        "skipped_files": failures,
        "source_executed": False,
        "catalog_is_trusted": False,
        "note": "Static AST inventory only. Review/port candidates into a typed DSL with tests; no arbitrary legacy Python execution.",
    }


def write_catalog(catalog: dict[str, Any], path: str | Path = DEFAULT_CATALOG_PATH) -> Path:
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def _query_words(query: str) -> set[str]:
    lower = query.lower()
    terms = set(re.findall(r"[a-z][a-z0-9_]*", lower))
    for jp, tag in JP_SYNONYMS.items():
        if jp in lower:
            terms.add(tag)
    if "closed loop" in lower or "closed wire" in lower:
        terms.add("closed_loop")
    if "point" in terms:
        terms.add("vertex")
    return {word for word in terms if len(word) > 1}


def search_legacy_catalog(catalog: dict[str, Any], query: str, limit: int = 10) -> list[dict[str, Any]]:
    if type(limit) is not int or limit < 1:
        raise RuleError("limit must be a positive integer")
    terms = _query_words(query)
    if not terms:
        raise RuleError("query must contain geometry keywords, e.g. 'parallel edge closed loop'")
    matches = []
    for entry in catalog.get("functions", []):
        tags = set(entry["tags"])
        name = entry["qualname"].lower()
        descriptions = (entry["docstring_excerpt"] + " " + " ".join(entry["called_symbols"])).lower()
        matched = sorted(word for word in terms if (
            word in tags or word in name or word in descriptions
        ))
        if not matched:
            continue
        # Stronger evidence when query matches identified geometry categories.
        score = 3 * sum(word in tags for word in matched)
        score += 2 * sum(word in name for word in matched)
        score += sum(word in descriptions for word in matched)
        item = dict(entry)
        item["score"] = score
        item["matched_terms"] = matched
        matches.append(item)
    return sorted(matches, key=lambda x: (-x["score"], x["function_id"]))[:limit]


def create_reuse_proposal(
    catalog: dict[str, Any],
    function_id: str,
    output_dir: str | Path = DEFAULT_PROPOSALS_ROOT,
) -> tuple[Path, dict[str, Any]]:
    """Create a REVIEW-ONLY migration plan; never import the source function."""
    matches = [entry for entry in catalog.get("functions", []) if entry["function_id"] == function_id]
    if len(matches) != 1:
        raise RuleError(f"Function not found or nonunique in catalog: {function_id}")
    fn = matches[0]
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", function_id).strip("-")[:80]
    digest = hashlib.sha256(function_id.encode("utf-8")).hexdigest()[:10]
    output = Path(output_dir).expanduser() / f"{slug}-{digest}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    proposal = {
        "schema_version": 1,
        "status": "review_required",
        "function_id": function_id,
        "original_file": fn["file"],
        "original_source_sha256": fn["source_sha256"],
        "original_lines": [fn["lineno"], fn["end_lineno"]],
        "extracted_tags": fn["tags"],
        "candidate_dsl_features": fn["potential_dsl_features"],
        "approved": False,
        "executed": False,
        "required_steps": [
            "Open original source locally and check dependencies, license, side effects and applicability.",
            "Port relevant geometric operations into src/cad_rule_agent/geometry_primitives using OCCT as a deterministic core.",
            "Expose typed, documented functions/predicates; never use source file name or STEP entity ID as a rule.",
            "Test against synthetic and real STEP cases, including edge cases and tolerance margins.",
            "Only then register reviewed primitives in the rule synthesizer and add provenance.",
        ],
    }
    # Avoid silently overwriting an already reviewed proposal.
    try:
        with output.open("x", encoding="utf-8") as dst:
            dst.write(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n")
    except FileExistsError as exc:
        raise RuleError(f"Proposal already exists: {output}") from exc
    return output, proposal
