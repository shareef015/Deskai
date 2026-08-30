from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("frontend_validator",ROOT/"scripts/validate_frontend_quality.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);F=V.module();SCHEMA=F.ViewModelSchema("incident-summary","1.0",(F.ViewModelField("incident_id","string"),F.ViewModelField("severity","string"),F.ViewModelField("evidence_ids","string_list",False)))
class FrontendQualityTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_view_model_is_fingerprinted(self):self.assertEqual(len(F.validate_view_model(SCHEMA,{"incident_id":"i1","severity":"high"}).fingerprint),64)
 def test_non_object_is_denied(self):
  with self.assertRaises(F.FrontendContractDenied):F.validate_view_model(SCHEMA,[])
 def test_missing_required_field_is_denied(self):
  with self.assertRaises(F.FrontendContractDenied):F.validate_view_model(SCHEMA,{"incident_id":"i1"})
 def test_unknown_field_is_denied(self):
  with self.assertRaises(F.FrontendContractDenied):F.validate_view_model(SCHEMA,{"incident_id":"i1","severity":"high","extra":True})
 def test_wrong_field_type_is_denied(self):
  with self.assertRaises(F.FrontendContractDenied):F.validate_view_model(SCHEMA,{"incident_id":4,"severity":"high"})
 def test_string_list_elements_are_typed(self):
  with self.assertRaises(F.FrontendContractDenied):F.validate_view_model(SCHEMA,{"incident_id":"i","severity":"high","evidence_ids":[1]})
 def test_fingerprint_is_order_independent(self):self.assertEqual(F.validate_view_model(SCHEMA,{"incident_id":"i","severity":"high"}).fingerprint,F.validate_view_model(SCHEMA,{"severity":"high","incident_id":"i"}).fingerprint)
 def test_contrast_threshold_is_met(self):self.assertGreaterEqual(F.contrast_ratio("#172033","#ffffff"),4.5)
if __name__=="__main__":unittest.main()
