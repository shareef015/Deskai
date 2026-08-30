from __future__ import annotations
import importlib.util,json,unittest
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_regression_dataset.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class RegressionDatasetTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/regression-cases.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_exact_case_count(self):self.assertEqual(self.data()["case_count"],500)
 def test_domains_and_scenario_classes_are_balanced(self):
  cases=self.data()["cases"];self.assertEqual(set(Counter(c["domain"] for c in cases).values()),{125});self.assertEqual(set(Counter(c["scenario_class"] for c in cases).values()),{125})
 def test_source_groups_do_not_cross_splits(self):
  groups=defaultdict(set)
  for c in self.data()["cases"]:groups[c["source_case_id"]].add(c["split"])
  self.assertTrue(all(len(v)==1 for v in groups.values()))
 def test_every_case_has_cross_artifact_lineage(self):self.assertTrue(all(len(c["artifact_refs"])==5 for c in self.data()["cases"]))
if __name__=="__main__":unittest.main()
