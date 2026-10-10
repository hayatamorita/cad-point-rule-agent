import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cad_rule_agent.core import RuleError, make_training_cases, synthesize, rule_to_dict
from cad_rule_agent.harness import ROOT, read_goal, run_demo, run_codex, verify

GOAL = ROOT / "harness/goal.synthetic.json"


def good_rule(path):
    training = json.loads((ROOT / "examples/synthetic_three_variants.json").read_text())
    rule = synthesize(make_training_cases(training))
    path.write_text(json.dumps(rule_to_dict(rule)), encoding="utf-8")
    return path


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def test_demo_generates_hypotheses_and_logs_failures(self):
        folder = self.folder / "demo"
        result = run_demo(GOAL, folder, max_rounds=8)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["rounds"], 4)
        self.assertEqual(result["verification"]["predicate_count"], 4)
        self.assertEqual(len(result["verification"]["training"]), 3)
        self.assertFalse(result["verification"]["real_step_verified"])
        events = [json.loads(line) for line in (folder / "exploration_log.jsonl").read_text().splitlines()]
        self.assertEqual([event["outcome"] for event in events],
                         ["rejected", "rejected", "rejected", "passed"])
        self.assertTrue((folder / "verification.json").is_file())
        self.assertTrue((folder / "blueprint.md").is_file())

    def test_resume_rechecks_candidate(self):
        folder = self.folder / "resume"
        result = run_demo(GOAL, folder)
        resumed = run_demo(GOAL, folder)
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["rounds"], 4)
        Path(result["candidate"]).write_text('{"schema_version": 1}')
        with self.assertRaises(RuleError):
            run_demo(GOAL, folder)

    def test_exhaust_budget_then_continue(self):
        folder = self.folder / "bounded"
        exhausted = run_demo(GOAL, folder, max_rounds=2)
        self.assertEqual(exhausted["status"], "exhausted")
        resumed = run_demo(GOAL, folder, max_rounds=8)
        self.assertEqual(resumed["status"], "passed")
        self.assertEqual(resumed["rounds"], 4)

    def test_goal_change_is_rejected_on_resume(self):
        goal = json.loads(GOAL.read_text())
        path = self.folder / "goal.json"
        path.write_text(json.dumps(goal))
        run_demo(path, self.folder / "run")
        goal["max_predicates"] = 7
        path.write_text(json.dumps(goal))
        with self.assertRaisesRegex(RuleError, "Goal or datasets changed"):
            run_demo(path, self.folder / "run")

    def test_verifier_checks_holdout(self):
        candidate = good_rule(self.folder / "candidate.json")
        goal = json.loads(GOAL.read_text())
        goal["holdout_expected_key"] = "wrong_holdout"
        path = self.folder / "altered.json"
        path.write_text(json.dumps(goal))
        with self.assertRaisesRegex(RuleError, "Holdout selected incorrect"):
            verify(candidate, path)

    def test_verifier_rejects_unknown_feature_and_empty_rule(self):
        p = self.folder / "wrong.json"
        p.write_text('{"schema_version":1,"rule_type":"conjunction_of_boolean_geometry_features","predicates":[]}')
        with self.assertRaises(RuleError):
            verify(p, GOAL)
        p.write_text('{"schema_version":1,"rule_type":"conjunction_of_boolean_geometry_features","predicates":[{"feature":"step_entity_id","equals":true}]}')
        with self.assertRaises(RuleError):
            verify(p, GOAL)

    def test_real_step_mode_not_supported(self):
        goal = json.loads(GOAL.read_text())
        goal["mode"] = "real_step"
        p = self.folder / "step.json"
        p.write_text(json.dumps(goal))
        with self.assertRaisesRegex(RuleError, "Real STEP"):
            read_goal(p)

    def test_codex_bad_process_bounded(self):
        class Result:
            returncode = 1
            stderr = "not installed"
        with patch("cad_rule_agent.harness.subprocess.run", return_value=Result()) as runner:
            response = run_codex(GOAL, self.folder / "failed", max_rounds=2)
        self.assertEqual(response["status"], "exhausted")
        self.assertEqual(runner.call_count, 2)

    def test_codex_cannot_change_goal_during_run(self):
        goal = self.folder / "protected_goal.json"
        value = json.loads(GOAL.read_text())
        goal.write_text(json.dumps(value))
        class Result:
            returncode = 0
            stderr = ""
        def malicious_runner(args, *, input, **kwargs):
            value["holdout_expected_key"] = "cheated"
            goal.write_text(json.dumps(value))
            return Result()
        with patch("cad_rule_agent.harness.subprocess.run", side_effect=malicious_runner):
            with self.assertRaisesRegex(RuleError, "protected goal"):
                run_codex(goal, self.folder / "tamper", max_rounds=2)

    def test_codex_proposal_independently_verified(self):
        class Result:
            returncode = 0
            stderr = ""
        def fake_runner(args, *, input, **kwargs):
            self.assertEqual(args[:3], ["codex", "exec", "--sandbox"])
            import re
            match = re.search(r"Write a SINGLE rule JSON to: (.+)", input)
            self.assertIsNotNone(match)
            good_rule(Path(match.group(1).strip()))
            return Result()
        with patch("cad_rule_agent.harness.subprocess.run", side_effect=fake_runner):
            response = run_codex(GOAL, self.folder / "accepted", max_rounds=2)
        self.assertEqual(response["status"], "passed")
        self.assertEqual(response["rounds"], 1)
        self.assertEqual(response["verification"]["verification_scope"], "synthetic_feature_graph_only")


if __name__ == "__main__":
    unittest.main()
