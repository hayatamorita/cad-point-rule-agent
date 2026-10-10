import copy
import json
import unittest
from pathlib import Path
from cad_rule_agent.core import (
    AmbiguousSelectionError, NoRuleFoundError, Rule, RuleError, Predicate,
    apply_unique, load_model, make_training_cases, resolve_target,
    rule_from_dict, rule_to_dict, select, synthesize, verify_training_cases,
)
ROOT = Path(__file__).resolve().parents[1]

def training():
    raw = json.loads((ROOT / "examples/synthetic_three_variants.json").read_text())
    return make_training_cases(raw)

class SynthesisTests(unittest.TestCase):
    def test_exact_common_rule_all_three(self):
        cases = training()
        rule = synthesize(cases)
        self.assertEqual(len(rule.predicates), 4)
        self.assertEqual({p.feature for p in rule.predicates}, {
            "front_region", "on_inner_closed_wire", "parallel_to_reference", "left_endpoint"
        })
        self.assertEqual(len(verify_training_cases(cases, rule)), 3)

    def test_serialization_and_unknown(self):
        rule = synthesize(training())
        restored = rule_from_dict(rule_to_dict(rule))
        model = load_model(json.loads((ROOT / "examples/synthetic_unseen_variant.json").read_text()))
        chosen = apply_unique(model, restored)
        self.assertEqual(chosen.key, "holdout_target")

    def test_no_rule_with_insufficient_predicates(self):
        with self.assertRaises(NoRuleFoundError):
            synthesize(training(), max_predicates=2)

    def test_bad_label_ambiguous(self):
        cases = training()
        model, label = cases[0]
        wrong = copy.deepcopy(model.vertices[0])
        model2 = type(model)(model.model_id, model.vertices + (wrong,), model.units, model.coordinate_frame)
        with self.assertRaises(AmbiguousSelectionError):
            resolve_target(model2, label)

    def test_bad_label_missing(self):
        model, label = training()[0]
        moved = type(label)((100000., 100000., 100000.), label.tolerance_mm, label.coordinate_frame)
        with self.assertRaises(AmbiguousSelectionError):
            resolve_target(model, moved)

    def test_same_frame_required(self):
        model, label = training()[0]
        altered = type(label)(label.xyz, label.tolerance_mm, "different_frame")
        with self.assertRaises(RuleError):
            resolve_target(model, altered)

    def test_apply_ambiguous_and_empty(self):
        model, _ = training()[0]
        with self.assertRaises(AmbiguousSelectionError):
            apply_unique(model, Rule(predicates=tuple()))
        with self.assertRaises(AmbiguousSelectionError):
            apply_unique(model, Rule(predicates=(Predicate("on_symmetry_plane", True),)))

    def test_forbid_non_geometry_keys(self):
        model, _ = training()[0]
        with self.assertRaises(RuleError):
            select(model, Rule(predicates=(Predicate("file_name", True),)))
        with self.assertRaises(RuleError):
            rule_from_dict({"schema_version": 1, "rule_type": "conjunction_of_boolean_geometry_features", "predicates": [{"feature": "xyz", "equals": True}]})

    def test_no_false_for_missing_attributes(self):
        model = load_model({"model_id": "x", "units": "mm", "coordinate_frame": "vehicle", "vertices": [
            {"key": "a", "xyz": [0,0,0], "features": {}},
            {"key": "b", "xyz": [1,0,0], "features": {"front_region": False}},
        ]})
        rule = Rule((Predicate("front_region", False),))
        self.assertEqual([v.key for v in select(model, rule)], ["b"])

    def test_reject_wrong_units_and_nan(self):
        raw = {"model_id": "x", "units": "m", "coordinate_frame": "vehicle", "vertices": [{"key": "a", "xyz": [0,0,0], "features": {}}]}
        with self.assertRaises(RuleError):
            load_model(raw)
        raw["units"] = "mm"
        raw["vertices"][0]["xyz"] = [float('nan'), 0, 0]
        with self.assertRaises(RuleError):
            load_model(raw)

if __name__ == "__main__":
    unittest.main()
