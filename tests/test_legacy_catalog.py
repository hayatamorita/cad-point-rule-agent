import json
import tempfile
import unittest
from pathlib import Path

from cad_rule_agent.core import RuleError
from cad_rule_agent.legacy_catalog import (
    build_legacy_catalog, write_catalog, search_legacy_catalog, create_reuse_proposal,
)

class LegacyCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "old_project").mkdir()
        self.example = self.root / "old_project" / "find_point.py"
        self.example.write_text(
            "from OCC.Core.TopExp import TopExp_Explorer\n"
            "from OCC.Core.TopAbs import TopAbs_EDGE\n"
            "print('this code must never be run')\n"
            "def find_parallel_edge_on_closed_wire(shape, reference_edge):\n"
            "    '''Find the parallel edge on a closed loop.'''\n"
            "    explorer = TopExp_Explorer(shape, TopAbs_EDGE)\n"
            "    return explorer\n"
            "class GeometryHelper:\n"
            "    def find_front_vertex(self, shape):\n"
            "        return shape\n",
            encoding="utf-8",
        )

    def test_indexes_without_running_or_importing(self):
        catalog = build_legacy_catalog(self.root)
        self.assertEqual(catalog["analyzed_python_files"], 1)
        self.assertEqual(catalog["function_count"], 2)
        self.assertFalse(catalog["source_executed"])
        f = catalog["functions"][0]
        self.assertEqual(f["function_id"], "old_project/find_point.py::find_parallel_edge_on_closed_wire")
        self.assertIn("parallel", f["tags"])
        self.assertIn("closed_loop", f["tags"])
        self.assertIn("on_closed_wire", f["potential_dsl_features"])
        self.assertIn("GeometryHelper.find_front_vertex", catalog["functions"][1]["qualname"])

    def test_search_english_and_japanese(self):
        catalog = build_legacy_catalog(self.root)
        english = search_legacy_catalog(catalog, "parallel edge closed loop")
        japanese = search_legacy_catalog(catalog, "閉ループと平行なエッジ")
        self.assertEqual(english[0]["qualname"], "find_parallel_edge_on_closed_wire")
        self.assertEqual(japanese[0]["qualname"], "find_parallel_edge_on_closed_wire")

    def test_proposal_is_review_only(self):
        catalog = build_legacy_catalog(self.root)
        fid = catalog["functions"][0]["function_id"]
        dest, proposal = create_reuse_proposal(catalog, fid, self.root / "_proposals")
        self.assertTrue(dest.exists())
        self.assertFalse(proposal["approved"])
        self.assertFalse(proposal["executed"])
        self.assertEqual(proposal["status"], "review_required")
        self.assertEqual(proposal["original_source_sha256"], catalog["functions"][0]["source_sha256"])
        with self.assertRaisesRegex(RuleError, "already exists"):
            create_reuse_proposal(catalog, fid, self.root / "_proposals")

    def test_catalog_json_roundtrip(self):
        catalog = build_legacy_catalog(self.root)
        saved = write_catalog(catalog, self.root / "_cache" / "index.json")
        self.assertEqual(json.loads(saved.read_text())["function_count"], 2)

    def test_invalid_query(self):
        with self.assertRaises(RuleError):
            search_legacy_catalog(build_legacy_catalog(self.root), "", 10)
        with self.assertRaises(RuleError):
            search_legacy_catalog(build_legacy_catalog(self.root), "edge", limit=0)

    def test_missing_directory(self):
        with self.assertRaisesRegex(RuleError, "folder not found"):
            build_legacy_catalog(self.root / "missing")

    def test_broken_source_does_not_stop_scan(self):
        (self.root / "broken.py").write_text("def broken(:\n", encoding="utf-8")
        catalog = build_legacy_catalog(self.root)
        self.assertEqual(catalog["function_count"], 2)
        self.assertEqual(len(catalog["skipped_files"]), 1)

    def test_symlink_outside_root_not_indexed(self):
        with tempfile.TemporaryDirectory() as other:
            link = self.root / "outsider.py"
            try:
                link.symlink_to(Path(other) / "secret.py")
                (Path(other) / "secret.py").write_text("def leaked(): pass")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks not available")
            catalog = build_legacy_catalog(self.root)
            self.assertEqual(catalog["function_count"], 2)

    def test_functions_with_no_geometry_tags(self):
        (self.root / "plain.py").write_text("def foo(x):\n    return x\n")
        catalog = build_legacy_catalog(self.root)
        self.assertEqual(catalog["function_count"], 3)
        self.assertEqual(search_legacy_catalog(catalog, "parallel")[0]["file"], "old_project/find_point.py")

    def test_file_over_limit_skipped(self):
        (self.root / "massive.py").write_bytes(b"#" + b"x" * 2_000_000)
        catalog = build_legacy_catalog(self.root)
        self.assertTrue(any(item["file"] == "massive.py" for item in catalog["skipped_files"]))

if __name__ == "__main__":
    unittest.main()
