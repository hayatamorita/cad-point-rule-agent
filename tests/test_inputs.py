import copy
import json
import tempfile
import unittest
from pathlib import Path

from cad_rule_agent.core import RuleError
from cad_rule_agent.inputs import parse_entity_id, validate_step_inputs
from cad_rule_agent.step_entities import resolve_step_entity

ROOT = Path(__file__).resolve().parents[1]

def mini_step(point_id: int, vertex_id: int | None = None) -> str:
    v = vertex_id if vertex_id is not None else point_id + 1
    return (
        "ISO-10303-21;\n"
        "HEADER;\nFILE_DESCRIPTION(('Synthetic'),'2;1');\nENDSEC;\n"
        "DATA;\n"
        "/* this comment is not an entity: #777 = VERTEX_POINT('',#999); */\n"
        f"#{point_id} = CARTESIAN_POINT('a; label', (1.0,2.0,3.0));\n"
        f"#{v} = VERTEX_POINT('',#{point_id});\n"
        "ENDSEC;\nEND-ISO-10303-21;\n"
    )

class TrainingInputsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "labels.json"
        self.payload = json.loads((ROOT / "data/training/labels.example.json").read_text())
        for n, case in enumerate(self.payload["training_cases"]):
            num = 118 + n * 100
            case["target_point"]["entity_id"] = num
            (self.root / case["step_file"]).write_text(mini_step(num), encoding="utf-8")

    def save(self):
        self.manifest.write_text(json.dumps(self.payload), encoding="utf-8")

    def test_point_entity_id_training_labels(self):
        self.save()
        report = validate_step_inputs(self.manifest)
        self.assertEqual([x["entity_id"] for x in report["cases"]], [118, 218, 318])
        self.assertEqual([x["linked_vertex_point_entity_ids"] for x in report["cases"]], [[119], [219], [319]])
        self.assertTrue(report["step_entity_ids_verified"])
        self.assertFalse(report["step_geometry_verified"])
        self.assertFalse(report["rule_discovery_ready"])

    def test_vertex_point_entity_accepted(self):
        self.payload["training_cases"][0]["target_point"]["entity_id"] = "#119"
        self.save()
        report = validate_step_inputs(self.manifest)
        self.assertEqual(report["cases"][0]["entity_type"], "VERTEX_POINT")
        self.assertEqual(report["cases"][0]["geometry_point_entity_id"], 118)

    def test_template_requires_user_input(self):
        self.payload["training_cases"][0]["target_point"]["entity_id"] = None
        self.save()
        with self.assertRaisesRegex(RuleError, "entity_id"):
            validate_step_inputs(self.manifest)

    def test_missing_step_rejected(self):
        (self.root / "type_c.step").unlink()
        self.save()
        with self.assertRaisesRegex(RuleError, "file missing"):
            validate_step_inputs(self.manifest)

    def test_empty_step_rejected(self):
        (self.root / "type_b.step").write_bytes(b"")
        self.save()
        with self.assertRaisesRegex(RuleError, "file is empty"):
            validate_step_inputs(self.manifest)

    def test_wrong_mapping_rejected(self):
        self.payload["training_cases"][1]["step_file"] = "type_a.step"
        self.save()
        with self.assertRaisesRegex(RuleError, "must be exactly"):
            validate_step_inputs(self.manifest)

    def test_missing_entity_rejected(self):
        self.payload["training_cases"][0]["target_point"]["entity_id"] = 777
        self.save()
        with self.assertRaisesRegex(RuleError, "does not exist"):
            validate_step_inputs(self.manifest)

    def test_non_point_entity_rejected(self):
        with (self.root / "type_a.step").open("a") as out:
            out.write("#1000=PRODUCT('x','x','',());\n")
        # This statement is after END-ISO-10303-21 and won't be accepted.
        text = (self.root / "type_a.step").read_text()
        text = text.replace("ENDSEC;\nEND-ISO-10303-21;", "#1000=PRODUCT('x','x','',());\nENDSEC;\nEND-ISO-10303-21;")
        (self.root / "type_a.step").write_text(text)
        self.payload["training_cases"][0]["target_point"]["entity_id"] = 1000
        self.save()
        with self.assertRaisesRegex(RuleError, "not a point entity"):
            validate_step_inputs(self.manifest)

    def test_multiline_comments_and_quoted_semicolon(self):
        path = self.root / "multi.step"
        path.write_text(
            "ISO-10303-21;\nHEADER;ENDSEC;DATA;\n"
            "/* #7=CARTESIAN_POINT('',(0.,0.,0.)); */\n"
            "#18=CARTE" + "SIAN_POINT('semi; and ''quote''',\n(2.0,3.0,4.0));\n"
            "#19=VERTEX_POINT('',#18);\nENDSEC;END-ISO-10303-21;",
        )
        self.assertEqual(resolve_step_entity(path, 18)["linked_vertex_point_entity_ids"], [19])
        with self.assertRaisesRegex(RuleError, "does not exist"):
            resolve_step_entity(path, 7)

    def test_reference_missing_rejected(self):
        path = self.root / "type_a.step"
        path.write_text("ISO-10303-21;HEADER;ENDSEC;DATA;#119=VERTEX_POINT('',#999);ENDSEC;END-ISO-10303-21;")
        with self.assertRaisesRegex(RuleError, "nonexistent"):
            resolve_step_entity(path, 119)

    def test_no_data_section(self):
        path = self.root / "type_a.step"
        path.write_text("ISO-10303-21;HEADER;ENDSEC;END-ISO-10303-21;")
        with self.assertRaisesRegex(RuleError, "No DATA"):
            resolve_step_entity(path, 118)

    def test_old_schema_rejected(self):
        self.payload["schema_version"] = 1
        self.save()
        with self.assertRaisesRegex(RuleError, "schema_version: 2"):
            validate_step_inputs(self.manifest)

    def test_invalid_ids(self):
        for value in [0, -1, None, True, "#0", "118", "#x", [118], 118.0]:
            with self.subTest(value=value):
                with self.assertRaises(RuleError):
                    parse_entity_id(value)

    def test_missing_labels_guidance(self):
        with self.assertRaisesRegex(RuleError, "Copy"):
            validate_step_inputs(self.manifest)

    def test_duplicate_variant(self):
        self.payload["training_cases"][1]["variant"] = "a"
        self.save()
        with self.assertRaisesRegex(RuleError, "duplicate variant"):
            validate_step_inputs(self.manifest)

if __name__ == "__main__":
    unittest.main()
