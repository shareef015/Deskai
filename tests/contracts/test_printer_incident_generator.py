from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_printer_incident_generator.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class PrinterIncidentGeneratorTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/printer-incidents.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_minimum_case_count(self):self.assertGreaterEqual(len(self.data()["cases"]),50)
 def test_all_incident_classes_are_covered(self):self.assertEqual(len({c["incident_id"] for c in self.data()["cases"]}),11)
 def test_all_cases_have_test_print_and_physical_confirmation(self):self.assertTrue(all(c["verification"]["test_print"]=="synthetic_test_page" and c["verification"]["physical_output_confirmation_required"] for c in self.data()["cases"]))
 def test_all_cases_have_replay_and_rollback(self):self.assertTrue(all(c["replay"]["master_seed"]==52001 and c["rollback"] for c in self.data()["cases"]))
if __name__=="__main__":unittest.main()
