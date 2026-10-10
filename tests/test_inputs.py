import json
import tempfile
import unittest
from pathlib import Path

from cad_rule_agent.core import RuleError
from cad_rule_agent.inputs import validate_step_inputs

ROOT = Path(__file__).resolve().parents[1]

class TrainingInputsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.manifest = self.path / 'labels.json'
        self.payload = json.loads((ROOT / 'data/training/labels.example.json').read_text())
        for case in self.payload['training_cases']:
            case['target_point']['xyz_mm'] = [10, 20, 30]
            (self.path / case['step_file']).write_text('ISO-10303-21;\nEND-ISO-10303-21;\n')

    def save(self):
        self.manifest.write_text(json.dumps(self.payload))

    def test_valid_placement_and_labels(self):
        self.save()
        report = validate_step_inputs(self.manifest)
        self.assertEqual(len(report['cases']), 3)
        self.assertFalse(report['step_geometry_verified'])
        self.assertFalse(report['rule_discovery_ready'])

    def test_template_placeholders_rejected(self):
        self.payload['training_cases'][0]['target_point']['xyz_mm'] = [None, None, None]
        self.save()
        with self.assertRaisesRegex(RuleError, 'fill xyz_mm'):
            validate_step_inputs(self.manifest)

    def test_missing_step_rejected(self):
        (self.path / 'type_c.step').unlink()
        self.save()
        with self.assertRaisesRegex(RuleError, 'file missing'):
            validate_step_inputs(self.manifest)

    def test_empty_step_rejected(self):
        (self.path / 'type_b.step').write_bytes(b'')
        self.save()
        with self.assertRaisesRegex(RuleError, 'file is empty'):
            validate_step_inputs(self.manifest)

    def test_wrong_pair_mapping_rejected(self):
        self.payload['training_cases'][1]['step_file'] = 'type_a.step'
        self.save()
        with self.assertRaisesRegex(RuleError, 'must be exactly'):
            validate_step_inputs(self.manifest)

    def test_wrong_units_rejected(self):
        self.payload['units'] = 'inches'
        self.save()
        with self.assertRaisesRegex(RuleError, 'millimetres'):
            validate_step_inputs(self.manifest)

    def test_wrong_frame_rejected(self):
        self.payload['coordinate_frame'] = 'vehicle'
        self.save()
        with self.assertRaisesRegex(RuleError, 'step_global'):
            validate_step_inputs(self.manifest)

    def test_negative_tolerance_rejected(self):
        self.payload['training_cases'][2]['target_point']['tolerance_mm'] = 0
        self.save()
        with self.assertRaisesRegex(RuleError, 'tolerance_mm'):
            validate_step_inputs(self.manifest)

    def test_missing_labels_guidance(self):
        with self.assertRaisesRegex(RuleError, 'Copy'):
            validate_step_inputs(self.manifest)

    def test_duplicate_variant_rejected(self):
        self.payload['training_cases'][1]['variant'] = 'a'
        self.save()
        with self.assertRaisesRegex(RuleError, 'duplicate variant'):
            validate_step_inputs(self.manifest)

if __name__ == '__main__':
    unittest.main()
