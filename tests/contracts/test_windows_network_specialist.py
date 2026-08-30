from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("windows_network_validator",ROOT/"scripts/validate_windows_network_specialist.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);W=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",consent_status="granted",domain="network",windows_version="windows_11",windows_build="24H2",connection_type="wifi",target_business_function="Outlook connectivity",vpn_expected=True);values.update(changes);return W.WindowsNetworkContext(**values)
class WindowsNetworkSpecialistTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_consent_required(self):
  with self.assertRaises(W.WindowsNetworkError):W.plan_diagnostics(context(consent_status="pending"))
 def test_network_requires_connection_type(self):self.assertEqual(W.plan_diagnostics(context(connection_type=None)).outcome,"clarify")
 def test_network_plan_is_layered_and_firewall_read_only(self):
  steps=set(W.plan_diagnostics(context()).steps);self.assertTrue({"inspect_adapter","inspect_ip_dhcp_gateway","test_dns","inspect_proxy","inspect_vpn","inspect_firewall_policy_read_only","test_target_port"}<=steps)
 def test_windows_plan_covers_services_events_resources_and_updates(self):
  steps=set(W.plan_diagnostics(context(domain="windows",connection_type=None)).steps);self.assertTrue({"inspect_service_state","collect_bounded_event_window","inspect_resource_pressure","inspect_windows_update_state"}<=steps)
 def test_rag_filters_build_and_vpn_context(self):
  filters=W.plan_diagnostics(context()).rag_queries[0]["filters"];self.assertEqual(filters["windows_build"],"24H2");self.assertTrue(filters["vpn_expected"])
 def test_hypotheses_require_evidence(self):
  with self.assertRaises(W.WindowsNetworkError):W.validate_hypotheses((W.Hypothesis("dns_failure",.9,()),))
 def test_security_bypass_is_prohibited(self):
  p=W.RemediationProposal("disable_firewall","high","security_administrator",True,"restore_policy",("technical_state_verified","target_business_function_works","employee_confirms"))
  with self.assertRaises(W.WindowsNetworkError):W.validate_remediation(p)
 def test_persistent_change_requires_rollback_and_end_to_end_verification(self):
  p=W.RemediationProposal("restart_network_service","medium","endpoint_administrator",False,None,("technical_state_verified",))
  with self.assertRaises(W.WindowsNetworkError):W.validate_remediation(p)
if __name__=="__main__":unittest.main()
