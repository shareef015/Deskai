from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_outlook_incident_generator.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-outlook-incident-generator-policy.json").read_text())
class OutlookIncidentGeneratorTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/outlook-incidents.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_minimum_case_count(self):self.assertGreaterEqual(len(self.data()["cases"]),50)
 def test_all_catalog_incidents_are_covered(self):self.assertEqual(len({c["incident_id"] for c in self.data()["cases"]}),11)
 def test_replay_metadata_is_present(self):self.assertTrue(all(c["replay"]["master_seed"]==POLICY["seed"] for c in self.data()["cases"]))
 def test_each_case_has_governed_closure(self):self.assertTrue(all(c["verification"] and c["required_approval"] and c["rollback"] for c in self.data()["cases"]))
if __name__=="__main__":unittest.main()
