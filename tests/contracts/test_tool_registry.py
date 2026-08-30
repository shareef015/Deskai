from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("tool_validator",ROOT/"scripts/validate_tool_registry.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);T=V.module()
S=T.ToolSchema("service_status","1.0.0","read_service", "read_only",frozenset({"service_name","device_id"}),frozenset({"service_name","device_id"}),10,True,False,False,"a"*64)
G=T.AgentGrant("tenant-1","windows-specialist",frozenset({"read_service"}),frozenset({"service_status@1.0.0"}),"b"*64)
def request(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",agent_id="windows-specialist",tool_id="service_status",tool_version="1.0.0",capability="read_service",parameters={"service_name":"Spooler","device_id":"WIN11-03"},consent_status="granted",approval_status="not_required",approval_plan_sha256=None,expected_plan_sha256=None,calls_in_current_minute=0);values.update(changes);return T.ToolRequest(**values)
class ToolRegistryTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_minimum_grant_allows_typed_call(self):self.assertEqual(T.authorize(S,G,request()).outcome,"allow")
 def test_dynamic_or_unregistered_tool_denied(self):self.assertEqual(T.authorize(T.ToolSchema(**{**S.__dict__,"dynamic":True}),G,request()).outcome,"deny")
 def test_cross_tenant_or_agent_scope_denied(self):self.assertEqual(T.authorize(S,G,request(tenant_id="tenant-2")).reason,"scope_mismatch")
 def test_tool_version_or_capability_mismatch_denied(self):self.assertEqual(T.authorize(S,G,request(tool_version="2.0.0")).outcome,"deny")
 def test_consent_and_rate_limit_enforced(self):self.assertEqual(T.authorize(S,G,request(consent_status="declined")).reason,"consent_required");self.assertEqual(T.authorize(S,G,request(calls_in_current_minute=10)).reason,"rate_limit_exceeded")
 def test_raw_command_or_unknown_parameter_denied(self):self.assertEqual(T.authorize(S,G,request(parameters={"command":"whoami"})).outcome,"deny");self.assertEqual(T.authorize(S,G,request(parameters={"unknown":"x"})).outcome,"deny")
 def test_exact_plan_approval_required_for_mutation(self):
  schema=T.ToolSchema(**{**S.__dict__,"tool_id":"restart_service","version":"1.0.0","capability":"restart_service","risk":"medium","requires_approval":True});grant=T.AgentGrant("tenant-1","windows-specialist",frozenset({"restart_service"}),frozenset({"restart_service@1.0.0"}),"c"*64);req=request(tool_id="restart_service",capability="restart_service",approval_status="approved",approval_plan_sha256="d"*64,expected_plan_sha256="e"*64)
  self.assertEqual(T.authorize(schema,grant,req).reason,"exact_approval_required")
 def test_authorization_decision_is_auditable(self):self.assertEqual(len(T.authorize(S,G,request()).decision_sha256),64)
if __name__=="__main__":unittest.main()
