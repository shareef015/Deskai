from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("print_scan_validator",ROOT/"scripts/validate_print_scan_specialist.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);P=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",consent_status="granted",domain="printer",topology="direct_network",windows_version="windows_11",device_model="Synthetic Laser",driver_or_protocol_version="IPP",protected_print_mode=False);values.update(changes);return P.PrintScanContext(**values)
class PrintScanSpecialistTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_consent_and_topology_required(self):
  with self.assertRaises(P.PrintScanError):P.plan_diagnostics(context(consent_status="pending"))
  self.assertEqual(P.plan_diagnostics(context(topology=None)).outcome,"clarify")
 def test_printer_plan_covers_queue_spooler_port_and_reachability(self):
  plan=P.plan_diagnostics(context());self.assertTrue({"inspect_queue","inspect_spooler","inspect_port","test_reachability"}<=set(plan.steps))
 def test_scanner_plan_covers_wia_twain_and_network(self):
  plan=P.plan_diagnostics(context(domain="scanner",topology="multifunction"));self.assertTrue({"inspect_wia","inspect_twain_metadata","test_reachability"}<=set(plan.steps));self.assertNotIn("print_queue",plan.tools)
 def test_rag_filters_include_topology_and_version(self):
  filters=P.plan_diagnostics(context()).rag_queries[0]["filters"];self.assertEqual(filters["topology"],"direct_network");self.assertEqual(filters["windows_version"],"windows_11")
 def test_hypotheses_require_evidence(self):
  with self.assertRaises(P.PrintScanError):P.validate_hypotheses((P.Hypothesis("wrong_port",.9,()),))
 def test_printer_requires_physical_output_confirmation(self):
  proposal=P.RemediationProposal("update_port","medium","endpoint_administrator",True,"restore_port",("test_print_submitted","employee_confirms"))
  with self.assertRaises(P.PrintScanError):P.validate_remediation("printer",proposal,protected_print_mode=False)
 def test_scanner_requires_safe_test_artifact(self):
  proposal=P.RemediationProposal("restart_wia","low","employee",False,None,("synthetic_test_scan","employee_confirms"))
  with self.assertRaises(P.PrintScanError):P.validate_remediation("scanner",proposal,protected_print_mode=False)
 def test_protected_print_mode_cannot_be_disabled_or_bypassed(self):
  required=("test_print_submitted","physical_output_confirmed","employee_confirms")
  with self.assertRaises(P.PrintScanError):P.validate_remediation("printer",P.RemediationProposal("disable_protected_print_mode","high","endpoint_administrator",True,"restore_policy",required),protected_print_mode=True)
  with self.assertRaises(P.PrintScanError):P.validate_remediation("printer",P.RemediationProposal("install_third_party_driver","high","endpoint_administrator",True,"restore_driver",required),protected_print_mode=True)
if __name__=="__main__":unittest.main()
