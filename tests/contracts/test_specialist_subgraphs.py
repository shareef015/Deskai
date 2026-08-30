from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("specialist_validator",ROOT/"scripts/validate_specialist_subgraphs.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);S=V.module()
def source(domain="printer"):return S.SpecialistInput("tenant-1","incident-1","thread-1","correlation-1","device-1",domain,"Printer offline","consent-1")
def evidence():return ({"evidence_id":"ev-1","tenant_id":"tenant-1","incident_id":"incident-1","source":"printer_inventory","kind":"diagnostic","observed_at":"2026-08-26T00:00:00Z","summary":"Printer registered","content_included":False,"digest":"a"*64},)
class SpecialistSubgraphTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_working_state_is_bounded_and_scoped(self):
  state=S.new_working_state(source());self.assertEqual(state["tool_calls_remaining"],8);self.assertEqual(state["scope"]["tenant_id"],"tenant-1");self.assertNotIn("messages",state)
 def test_tool_authorization_is_domain_specific(self):self.assertTrue(S.authorize_tool("printer","print_queue"));self.assertFalse(S.authorize_tool("printer","outlook_health"))
 def test_complete_output_requires_bounded_evidence(self):
  output=S.finalize_output(source(),status="complete",evidence=evidence(),safe_summary="Queue inspected");self.assertEqual(S.supervisor_handoff(output)["phase"],"evidence_fusion");self.assertEqual(len(output.provenance_sha256),64)
 def test_raw_or_cross_tenant_evidence_is_rejected(self):
  bad=dict(evidence()[0]);bad["content_included"]=True
  with self.assertRaises(S.SpecialistContractError):S.finalize_output(source(),status="complete",evidence=(bad,),safe_summary="bad")
  bad=dict(evidence()[0]);bad["tenant_id"]="other"
  with self.assertRaises(S.SpecialistContractError):S.finalize_output(source(),status="complete",evidence=(bad,),safe_summary="bad")
 def test_incomplete_and_blocked_outputs_return_safely(self):
  insufficient=S.finalize_output(source(),status="insufficient_evidence",evidence=(),questions=("Is the printer powered on?",),safe_summary="Need confirmation");self.assertEqual(S.supervisor_handoff(insufficient)["phase"],"clarification")
  blocked=S.finalize_output(source(),status="blocked",evidence=(),safe_summary="Endpoint unavailable");self.assertEqual(S.supervisor_handoff(blocked)["phase"],"escalated")
if __name__=="__main__":unittest.main()
