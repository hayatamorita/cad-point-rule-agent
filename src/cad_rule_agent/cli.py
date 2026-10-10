"""CLI for precomputed synthetic feature graphs, not native STEP."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .inputs import DEFAULT_MANIFEST, validate_step_inputs
from .legacy_catalog import (
    DEFAULT_LEGACY_ROOT, DEFAULT_CATALOG_PATH, DEFAULT_PROPOSALS_ROOT,
    build_legacy_catalog, write_catalog, search_legacy_catalog, create_reuse_proposal,
)
from .core import (
    RuleError, apply_unique, load_model, make_training_cases,
    rule_from_dict, rule_to_dict, synthesize, verify_training_cases,
)

def read_json(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuleError("JSON root must be an object")
    return data

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic feature-graph rule discovery prototype (NOT STEP reader)")
    sub = parser.add_subparsers(dest="command", required=True)
    train = sub.add_parser("synthesize", help="Synthesize from labeled synthetic feature graphs")
    train.add_argument("--dataset", required=True)
    train.add_argument("--output", required=True)
    train.add_argument("--max-predicates", type=int, default=8)
    apply = sub.add_parser("apply", help="Apply a rule to an unlabeled synthetic feature graph")
    apply.add_argument("--model", required=True)
    apply.add_argument("--rule", required=True)
    check = sub.add_parser("check-inputs", help="Validate STEP file placement and labeled JSON (does not parse STEP)")
    check.add_argument("--dataset", default=str(DEFAULT_MANIFEST))
    legacy_index = sub.add_parser("legacy-index", help="Statically index historical pythonOCC scripts without executing them")
    legacy_index.add_argument("--root", default=str(DEFAULT_LEGACY_ROOT))
    legacy_index.add_argument("--output", default=str(DEFAULT_CATALOG_PATH))
    legacy_search = sub.add_parser("legacy-search", help="Find relevant historical pyocc functions by geometry keywords")
    legacy_search.add_argument("--query", required=True)
    legacy_search.add_argument("--root", default=str(DEFAULT_LEGACY_ROOT))
    legacy_search.add_argument("--limit", type=int, default=10)
    legacy_promote = sub.add_parser("legacy-promote", help="Draft a review-only migration proposal (no source execution)")
    legacy_promote.add_argument("--function-id", required=True)
    legacy_promote.add_argument("--root", default=str(DEFAULT_LEGACY_ROOT))
    legacy_promote.add_argument("--output-dir", default=str(DEFAULT_PROPOSALS_ROOT))
    args = parser.parse_args(argv)
    try:
        if args.command == "legacy-index":
            catalog = build_legacy_catalog(args.root)
            index_path = write_catalog(catalog, args.output)
            print(json.dumps({
                "index_file": str(index_path),
                "analyzed_python_files": catalog["analyzed_python_files"],
                "function_count": catalog["function_count"],
                "skipped_files": catalog["skipped_files"],
                "source_executed": False,
            }, ensure_ascii=False, indent=2))
        elif args.command == "legacy-search":
            catalog = build_legacy_catalog(args.root)
            matches = search_legacy_catalog(catalog, args.query, limit=args.limit)
            print(json.dumps({
                "query": args.query,
                "matches": matches,
                "source_executed": False,
            }, ensure_ascii=False, indent=2))
        elif args.command == "legacy-promote":
            catalog = build_legacy_catalog(args.root)
            proposal_path, proposal = create_reuse_proposal(catalog, args.function_id, args.output_dir)
            print(json.dumps({
                "proposal_file": str(proposal_path),
                "proposal": proposal,
            }, ensure_ascii=False, indent=2))
        elif args.command == "check-inputs":
            print(json.dumps(validate_step_inputs(args.dataset), ensure_ascii=False, indent=2))
        elif args.command == "synthesize":
            cases = make_training_cases(read_json(args.dataset))
            rule = synthesize(cases, max_predicates=args.max_predicates)
            report = verify_training_cases(cases, rule)
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(rule_to_dict(rule), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"rule_file": str(output), "verification": report}, ensure_ascii=False, indent=2))
        else:
            model = load_model(read_json(args.model))
            rule = rule_from_dict(read_json(args.rule))
            selected = apply_unique(model, rule)
            print(json.dumps({"model_id": model.model_id, "selected_key": selected.key, "selected_xyz_mm": selected.xyz}, ensure_ascii=False, indent=2))
        return 0
    except (RuleError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
