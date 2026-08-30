from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("closure_validator",ROOT/"scripts/validate_resolution_closure.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",domain="network",root_cause="dns_cache_stale",root_cause_provenance_sha256="a"*64,plan_id="rmp-1",plan_provenance_sha256="b"*64,approval_packet_id="packet-1",approval_decision_fingerprint="c"*64,execution_result_fingerprint="d"*64,verification_status="verified",verification_provenance_sha256="e"*64,employee_confirmation_actor_id="employee-1",employee_confirmation_status="confirmed",evidence_ids=("ev-1","ev-2"),recurrence_detected=False);values.update(changes);return C.ClosureContext(**values)
def close(ctx=None,**kwargs):return C.close_incident(ctx or context(),resolution_text=kwargs.get("resolution_text","Flushed the device DNS cache and confirmed Outlook connectivity."),knowledge_title=kwargs.get("knowledge_title","Stale DNS cache blocks Outlook"),problem_pattern=kwargs.get("problem_pattern","Outlook cannot connect while device DNS resolution is stale."))
class ResolutionClosureTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_verified_incident_closes(self):self.assertEqual(close().outcome,"closed")
 def test_missing_employee_confirmation_blocks_closure(self):
  with self.assertRaises(C.ClosureDenied):close(context(employee_confirmation_status="not_fixed"))
 def test_incomplete_provenance_blocks_closure(self):
  with self.assertRaises(C.ClosureDenied):close(context(execution_result_fingerprint="bad"))
 def test_duplicate_evidence_references_block_closure(self):
  with self.assertRaises(C.ClosureDenied):close(context(evidence_ids=("ev-1","ev-1")))
 def test_knowledge_candidate_is_pending_human_review(self):self.assertEqual(close().knowledge_candidate.status,"pending_human_review")
 def test_sensitive_text_is_redacted(self):
  record=close(resolution_text="password=abc user@example.com was removed");self.assertIn("[redacted-secret]",record.resolution_summary);self.assertNotIn("user@example.com",record.resolution_summary)
 def test_recurrence_reopens_without_knowledge_candidate(self):
  record=close(context(recurrence_detected=True));self.assertEqual(record.outcome,"reopened");self.assertIsNone(record.knowledge_candidate)
 def test_closed_handoff_is_terminal_resolved(self):
  handoff=C.supervisor_handoff(close());self.assertEqual(handoff["phase"],"resolved");self.assertEqual(handoff["final_status"],"resolved")
if __name__=="__main__":unittest.main()
