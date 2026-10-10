"""Bounded persistent generate/test/refine harness inspired by Chenyang Yuan.

Only synthetic precomputed geometry features are supported. A real STEP target
must not be declared verified before a separate OCCT-backed checker exists.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from .core import (
    RuleError, NoRuleFoundError, make_training_cases, synthesize,
    rule_from_dict, rule_to_dict, verify_training_cases, load_model, apply_unique,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOAL = ROOT / "harness" / "goal.synthetic.json"
DEFAULT_RUN = ROOT / "runs" / "harness"


def read_json(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuleError("Expected JSON object")
    return data


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _event(folder: Path, **values: Any) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "exploration_log.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "utc": datetime.now(timezone.utc).isoformat(), **values
        }, ensure_ascii=False) + "\n")


def _dataset(path: str) -> Path:
    if not isinstance(path, str) or not path:
        raise RuleError("Goal dataset path must be a nonempty string")
    item = Path(path)
    return (item if item.is_absolute() else ROOT / item).resolve()


def read_goal(path: str | Path = DEFAULT_GOAL) -> dict[str, Any]:
    goal = read_json(path)
    if goal.get("schema_version") != 1 or goal.get("mode") != "synthetic":
        raise RuleError("Unsupported goal. Real STEP verification is NOT yet implemented.")
    if goal.get("unique_required") is not True:
        raise RuleError("Unique selection goal must not be weakened")
    n = goal.get("min_training_cases")
    if type(n) is not int or n < 3:
        raise RuleError("At least 3 training cases required")
    m = goal.get("max_predicates")
    if type(m) is not int or not 1 <= m <= 24:
        raise RuleError("max_predicates must be in [1,24]")
    for name in ("training_dataset", "holdout_model"):
        _dataset(goal.get(name))
    if not isinstance(goal.get("holdout_expected_key"), str) or not goal["holdout_expected_key"]:
        raise RuleError("Missing expected holdout result")
    return goal


def fingerprint(path: str | Path) -> str:
    goal = read_goal(path)
    digest = hashlib.sha256()
    for name in (str(Path(path).resolve()), goal["training_dataset"], goal["holdout_model"]):
        p = _dataset(name)
        digest.update(str(p).encode("utf-8"))
        try:
            digest.update(p.read_bytes())
        except OSError as exc:
            raise RuleError(f"Unreadable goal/dataset {p}: {exc}") from exc
    return digest.hexdigest()


def verify(candidate: str | Path, goal_path: str | Path = DEFAULT_GOAL) -> dict[str, Any]:
    """Fail-closed acceptance gate; never accepts tool stdout as proof."""
    goal = read_goal(goal_path)
    cases = make_training_cases(read_json(_dataset(goal["training_dataset"])))
    if len(cases) < goal["min_training_cases"]:
        raise RuleError("Insufficient training cases")
    model_ids = [model.model_id for model, _ in cases]
    if len(model_ids) != len(set(model_ids)):
        raise RuleError("Training model IDs must be distinct")
    rule = rule_from_dict(read_json(candidate))
    if len(rule.predicates) > goal["max_predicates"]:
        raise RuleError("Rule exceeds predicate complexity budget")
    if len(rule.predicates) != len(set(rule.predicates)):
        raise RuleError("Duplicate predicates are not accepted")
    training = verify_training_cases(cases, rule)
    holdout = load_model(read_json(_dataset(goal["holdout_model"])))
    if holdout.model_id in model_ids:
        raise RuleError("Holdout must not duplicate training model identity")
    selected = apply_unique(holdout, rule)
    if selected.key != goal["holdout_expected_key"]:
        raise RuleError(f"Holdout selected incorrect point {selected.key!r}")
    return {
        "status": "passed",
        "verification_scope": "synthetic_feature_graph_only",
        "real_step_verified": False,
        "training": training,
        "holdout": {"model_id": holdout.model_id, "selected_key": selected.key},
        "predicate_count": len(rule.predicates),
        "fingerprint": fingerprint(goal_path),
    }


def _checkpoint(folder: Path, digest: str) -> tuple[Path, dict[str, Any]]:
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / "state.json"
    state = read_json(p) if p.exists() else {"fingerprint": digest, "last_round": 0, "status": "running"}
    if state.get("fingerprint") != digest:
        raise RuleError("Goal or datasets changed: choose a new --run-dir")
    if type(state.get("last_round")) is not int or state["last_round"] < 0:
        raise RuleError("Invalid checkpoint")
    if not p.exists():
        write_json(p, state)
    return p, state


def _blueprint(folder: Path, state: str, round_number: int, observation: str) -> None:
    (folder / "blueprint.md").write_text(
        "# Exploration blueprint\n\n"
        f"State: {state}\n\nRound: {round_number}\n\n"
        f"Observation: {observation}\n\n"
        "Only synthetic feature graphs are supported. Never change target labels, "
        "acceptance goal or tests to force success. See exploration_log.jsonl.\n",
        encoding="utf-8",
    )


def _passed(folder: Path, state_path: Path, digest: str, round_number: int,
            candidate: Path, report: dict[str, Any]) -> dict[str, Any]:
    write_json(folder / "verification.json", report)
    write_json(state_path, {"fingerprint": digest, "last_round": round_number,
                            "status": "passed", "candidate": str(candidate)})
    _event(folder, round=round_number, outcome="passed", candidate=str(candidate))
    _blueprint(folder, "passed", round_number,
               "One identical rule uniquely selects all training targets and synthetic holdout")
    return {"status": "passed", "rounds": round_number, "candidate": str(candidate),
            "verification": report, "run_dir": str(folder)}


def _failed(folder: Path, state_path: Path, digest: str, round_number: int,
            reason: str) -> None:
    _event(folder, round=round_number, outcome="rejected", reason=reason[:1000])
    write_json(state_path, {"fingerprint": digest, "last_round": round_number,
                            "status": "running"})
    _blueprint(folder, "searching", round_number, reason[:400])


def _start(goal_path: str | Path, run_dir: str | Path) -> tuple[dict[str, Any], str, Path, Path, dict[str, Any]]:
    goal = read_goal(goal_path)
    digest = fingerprint(goal_path)
    folder = Path(run_dir).expanduser().resolve()
    state_path, state = _checkpoint(folder, digest)
    return goal, digest, folder, state_path, state


def _already_done(folder: Path, state: dict[str, Any], goal_path: str | Path) -> dict[str, Any] | None:
    if state["status"] == "passed":
        candidate = state.get("candidate")
        report = verify(candidate, goal_path)
        return {"status": "passed", "rounds": state["last_round"],
                "candidate": candidate, "verification": report,
                "run_dir": str(folder), "resumed": True}
    return None


def run_demo(goal_path: str | Path = DEFAULT_GOAL,
             run_dir: str | Path = DEFAULT_RUN / "demo",
             max_rounds: int = 8) -> dict[str, Any]:
    if type(max_rounds) is not int or not 1 <= max_rounds <= 100:
        raise RuleError("max_rounds must be in [1,100]")
    goal, digest, folder, state_path, state = _start(goal_path, run_dir)
    done = _already_done(folder, state, goal_path)
    if done:
        return done
    cases = make_training_cases(read_json(_dataset(goal["training_dataset"])))
    last = state["last_round"]
    limit = min(max_rounds, goal["max_predicates"])
    for round_number in range(last + 1, limit + 1):
        try:
            rule = synthesize(cases, max_predicates=round_number)
        except NoRuleFoundError as exc:
            _failed(folder, state_path, digest, round_number,
                    f"Hypothesis complexity <= {round_number} rejected: {exc}")
            continue
        candidate = folder / "candidates" / f"round_{round_number:02d}.json"
        if candidate.exists():
            raise RuleError(f"Refusing to overwrite candidate {candidate}")
        write_json(candidate, rule_to_dict(rule))
        try:
            report = verify(candidate, goal_path)
        except RuleError as exc:
            _failed(folder, state_path, digest, round_number, f"Verifier rejected: {exc}")
            continue
        return _passed(folder, state_path, digest, round_number, candidate, report)
    write_json(state_path, {"fingerprint": digest, "last_round": max(last, limit),
                            "status": "exhausted"})
    _blueprint(folder, "exhausted", max(last, limit), "No accepted candidate within budget")
    return {"status": "exhausted", "rounds": max(last, limit), "run_dir": str(folder)}


def run_codex(goal_path: str | Path = DEFAULT_GOAL,
              run_dir: str | Path = DEFAULT_RUN / "codex",
              max_rounds: int = 4, codex_bin: str = "codex",
              timeout_seconds: int = 900) -> dict[str, Any]:
    """Explicit opt-in: each Codex turn proposes candidate JSON; local verifier decides."""
    if type(max_rounds) is not int or not 1 <= max_rounds <= 20:
        raise RuleError("Codex max_rounds must be in [1,20]")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
        raise RuleError("timeout_seconds must be in [1,3600]")
    goal, digest, folder, state_path, state = _start(goal_path, run_dir)
    done = _already_done(folder, state, goal_path)
    if done:
        return done
    prompt_head = (ROOT / "harness" / "prompt.md").read_text(encoding="utf-8")
    feedback = "No previous attempt."
    for round_number in range(state["last_round"] + 1, max_rounds + 1):
        candidate = folder / "candidates" / f"round_{round_number:02d}.json"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if candidate.exists():
            raise RuleError(f"Candidate already exists: {candidate}")
        prompt = (
            prompt_head + "\n\n"
            f"Round {round_number}/{max_rounds}; previous rejection: {feedback}\n"
            f"Fixed goal file: {Path(goal_path).resolve()}\n"
            f"Training dataset: {_dataset(goal['training_dataset'])}\n"
            f"Write a SINGLE rule JSON to: {candidate}\n"
            "Do not edit verifier, goal, other source code, labels, or fixtures. "
            "Do not run git, upload files, or use private STEP data.\n"
        )
        try:
            result = subprocess.run(
                [codex_bin, "exec", "--sandbox", "workspace-write", "-"],
                input=prompt, capture_output=True, text=True, cwd=ROOT,
                timeout=timeout_seconds, check=False,
            )
            if result.returncode:
                raise RuleError(f"Codex exited {result.returncode}: {result.stderr[-500:]}")
            if not candidate.is_file():
                raise RuleError("Codex did not create candidate rule JSON")
            report = verify(candidate, goal_path)
            _event(folder, round=round_number, outcome="agent_candidate",
                   candidate=str(candidate))
            return _passed(folder, state_path, digest, round_number, candidate, report)
        except (OSError, subprocess.TimeoutExpired, RuleError) as exc:
            feedback = str(exc)
            _failed(folder, state_path, digest, round_number, feedback)
    write_json(state_path, {"fingerprint": digest, "last_round": max_rounds,
                            "status": "exhausted"})
    _blueprint(folder, "exhausted", max_rounds, "Codex proposer reached max rounds")
    return {"status": "exhausted", "rounds": max_rounds, "run_dir": str(folder),
            "last_feedback": feedback}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded CAD hypothesis / verification harness")
    sub = parser.add_subparsers(dest="action", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--goal", default=str(DEFAULT_GOAL))
    demo.add_argument("--run-dir", default=str(DEFAULT_RUN / "demo"))
    demo.add_argument("--max-rounds", type=int, default=8)
    codex = sub.add_parser("codex")
    codex.add_argument("--goal", default=str(DEFAULT_GOAL))
    codex.add_argument("--run-dir", default=str(DEFAULT_RUN / "codex"))
    codex.add_argument("--max-rounds", type=int, default=4)
    codex.add_argument("--codex-bin", default="codex")
    codex.add_argument("--timeout-seconds", type=int, default=900)
    gate = sub.add_parser("verify")
    gate.add_argument("--goal", default=str(DEFAULT_GOAL))
    gate.add_argument("--candidate", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "demo":
            report = run_demo(args.goal, args.run_dir, args.max_rounds)
        elif args.action == "codex":
            report = run_codex(args.goal, args.run_dir, args.max_rounds,
                               args.codex_bin, args.timeout_seconds)
        else:
            report = verify(args.candidate, args.goal)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "passed" else 3
    except (RuleError, OSError, json.JSONDecodeError) as exc:
        print(f"VERIFICATION_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
