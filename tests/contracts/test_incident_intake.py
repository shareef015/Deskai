from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("intake_validator",ROOT/"scripts/validate_incident_intake.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);I=V.module()
SOURCE="Outlook is disconnected today on WIN11-03"
def extraction(**changes):
 values=dict(summary="Outlook disconnected",symptoms=("Outlook shows disconnected",),business_impact="individual_blocked",affected_device_id="WIN11-03",timeline="today",domain_candidates=(I.DomainCandidate("outlook",.95,(0,7)),),uncertain_fields=(),clarification_needs=(),evidence_references=("message-1",),source_digest=I.source_digest(SOURCE));values.update(changes);return I.IntakeExtraction(**values)
class IncidentIntakeTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_complete_extraction_moves_to_classification(self):self.assertEqual(I.intake_state_update(extraction(),sanitized_source=I.sanitize_source(SOURCE),registered_device_ids=frozenset({"WIN11-03"}))["phase"],"classification")
 def test_missing_values_require_explicit_uncertainty(self):
  with self.assertRaises(I.IntakeValidationError):I.validate_extraction(extraction(affected_device_id=None),sanitized_source=SOURCE,registered_device_ids=frozenset({"WIN11-03"}))
 def test_unregistered_device_is_rejected(self):
  with self.assertRaises(I.IntakeValidationError):I.validate_extraction(extraction(affected_device_id="UNKNOWN-PC"),sanitized_source=SOURCE,registered_device_ids=frozenset({"WIN11-03"}))
 def test_invalid_source_span_is_rejected(self):
  bad=extraction(domain_candidates=(I.DomainCandidate("outlook",.9,(0,999)),))
  with self.assertRaises(I.IntakeValidationError):I.validate_extraction(bad,sanitized_source=SOURCE,registered_device_ids=frozenset({"WIN11-03"}))
 def test_uncertainty_routes_to_clarification(self):
  value=extraction(business_impact="unknown",uncertain_fields=("business_impact",),clarification_needs=("How many people are affected?",));self.assertEqual(I.intake_state_update(value,sanitized_source=SOURCE,registered_device_ids=frozenset({"WIN11-03"}))["phase"],"clarification")
 def test_secret_like_source_is_redacted_before_digest(self):
  safe=I.sanitize_source("password=hunter2 Outlook fails");self.assertNotIn("hunter2",safe);self.assertEqual(len(I.source_digest(safe)),64)
 def test_source_digest_mismatch_fails(self):
  with self.assertRaises(I.IntakeValidationError):I.validate_extraction(extraction(source_digest="0"*64),sanitized_source=SOURCE,registered_device_ids=frozenset({"WIN11-03"}))
if __name__=="__main__":unittest.main()
