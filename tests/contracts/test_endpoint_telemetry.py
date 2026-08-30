from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_endpoint_telemetry.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class EndpointTelemetryTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/endpoint-telemetry.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_all_incident_cases_have_packs(self):self.assertEqual(self.data()["pack_count"],220)
 def test_each_pack_has_five_typed_results(self):self.assertTrue(all(len(p["results"])==5 for p in self.data()["packs"]))
 def test_all_result_states_are_covered(self):self.assertEqual({r["status"] for p in self.data()["packs"] for r in p["results"]},{"success","failure","timeout","partial"})
 def test_redaction_and_lineage_are_mandatory(self):self.assertTrue(all(r["redaction"]["applied"] and r["correlation_id"]==p["correlation_id"] for p in self.data()["packs"] for r in p["results"]))
if __name__=="__main__":unittest.main()
