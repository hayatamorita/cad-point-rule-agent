"""CLI for precomputed synthetic feature graphs, not native STEP."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
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
    args = parser.parse_args(argv)
    try:
        if args.command == "synthesize":
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
