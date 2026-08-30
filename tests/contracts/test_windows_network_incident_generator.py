from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_windows_network_incident_generator.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class WindowsNetworkIncidentGeneratorTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/windows-network-incidents.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_minimum_case_count(self):self.assertGreaterEqual(len(self.data()["cases"]),60)
 def test_all_incident_classes_are_covered(self):self.assertEqual(len({c["incident_id"] for c in self.data()["cases"]}),12)
 def test_original_business_function_is_mandatory(self):self.assertTrue(all(c["verification"]["business_function_success_required"] and not c["verification"]["ping_or_dns_alone_sufficient"] for c in self.data()["cases"]))
 def test_all_cases_have_replay_rollback_and_redaction(self):self.assertTrue(all(c["replay"]["master_seed"]==54001 and c["rollback"] and all(e["sensitive_values_redacted"] for e in c["diagnostic_evidence"]) for c in self.data()["cases"]))
if __name__=="__main__":unittest.main()
