from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("outlook_validator",ROOT/"scripts/validate_outlook_specialist.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);O=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",consent_status="granted",process_name="outlook.exe",windows_version="windows_11",outlook_build="16.0.1",incident_class="connectivity");values.update(changes);return O.OutlookContext(**values)
class OutlookSpecialistTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_consent_required(self):
  with self.assertRaises(O.OutlookSpecialistError):O.plan_diagnostics(context(consent_status="pending"))
 def test_classic_and_new_clients_are_separated(self):
  classic=O.plan_diagnostics(context(incident_class="add_in"));new=O.plan_diagnostics(context(process_name="olk.exe",incident_class="add_in"));self.assertIn("outlook_addins",classic.tools);self.assertNotIn("outlook_addins",new.tools);self.assertFalse(any(x.endswith("_if_classic") for x in new.steps))
 def test_rag_plan_is_version_and_tenant_filtered(self):
  plan=O.plan_diagnostics(context());filters=plan.rag_queries[0]["filters"];self.assertEqual(filters["tenant_id"],"tenant-1");self.assertEqual(filters["client"],"classic_outlook");self.assertEqual(filters["outlook_build"],"16.0.1")
 def test_unknown_client_does_not_guess(self):self.assertEqual(O.plan_diagnostics(context(process_name="mystery.exe")).outcome,"escalate")
 def test_hypotheses_require_evidence(self):
  with self.assertRaises(O.OutlookSpecialistError):O.validate_hypotheses((O.Hypothesis("dns_failure",.9,(),()),))
 def test_close_strong_hypotheses_preserve_contradiction(self):
  items=(O.Hypothesis("dns_failure",.88,("e1",),()),O.Hypothesis("service_outage",.82,("e2",),()));self.assertEqual(O.validate_hypotheses(items),"contradictory_evidence")
 def test_persistent_remediation_requires_rollback(self):
  proposal=O.RemediationProposal("rebuild_profile","medium","l2_l3_specialist",False,None,("client_opens","employee_confirms"))
  with self.assertRaises(O.OutlookSpecialistError):O.validate_remediation(proposal)
 def test_verification_requires_employee_confirmation(self):
  proposal=O.RemediationProposal("restart_outlook","low","employee",False,None,("client_opens","send_receive_test"))
  with self.assertRaises(O.OutlookSpecialistError):O.validate_remediation(proposal)
if __name__=="__main__":unittest.main()
