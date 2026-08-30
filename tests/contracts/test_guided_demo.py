from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_guided_demo.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class GuidedDemoTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/demo-packs.json").read_text())
 def test_demo_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_eight_curated_packs(self):self.assertEqual(self.data()["pack_count"],8)
 def test_all_packs_are_synthetic_and_resettable(self):self.assertTrue(all(p["synthetic_only"] and p["expected"]["reset_state"]=="ready" for p in self.data()["packs"]))
 def test_resolution_and_failure_paths_are_present(self):self.assertTrue({"outlook_resolution","printer_resolution","scanner_resolution","network_resolution","rollback_failure"}.issubset({p["slug"] for p in self.data()["packs"]}))
 def test_each_pack_has_complete_guided_sequence(self):self.assertTrue(all([s["id"] for s in p["steps"]]==["greeting","consent","evidence","approval","execution","verification","closure"] for p in self.data()["packs"]))
if __name__=="__main__":unittest.main()
