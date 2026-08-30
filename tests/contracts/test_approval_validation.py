from __future__ import annotations
import datetime as dt,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("approval_validator",ROOT/"scripts/validate_approval_validation.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);A=V.module();NOW=dt.datetime(2026,8,27,8,0,tzinfo=dt.timezone.utc)
def packet(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",thread_id="thread-1",checkpoint_id="cp-1",plan_id="rmp-1",plan_provenance_sha256="a"*64,critic_status="pass",critic_provenance_sha256="b"*64,risk="medium",action_ids=("restart-service",),capability_ids=("restart_service",),requester_id="desk-1",plan_author_id="planner-service",required_approver_roles=("endpoint_administrator",),issued_at=NOW,ttl_minutes=15);values.update(changes);return A.create_packet(**values)
def principal(**changes):
 values=dict(subject="admin-1",tenant_id="tenant-1",roles=frozenset({"endpoint_administrator"}),authenticated=True,is_ai=False);values.update(changes);return A.ApprovalPrincipal(**values)
def decision(p,**changes):
 values=dict(packet_id=p.packet_id,version=p.version,plan_id=p.plan_id,plan_provenance_sha256=p.plan_provenance_sha256,decision="approved",reason="Reviewed evidence and rollback.");values.update(changes);return A.ApprovalDecision(**values)
class ApprovalValidationTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_critic_pass_required(self):
  with self.assertRaises(A.ApprovalDenied):packet(critic_status="revise")
 def test_author_cannot_request_approval(self):
  with self.assertRaises(A.ApprovalDenied):packet(requester_id="planner-service")
 def test_authenticated_qualified_human_can_decide(self):
  p=packet();result=A.validate_decision(packet=p,principal=principal(),submission=decision(p),now=NOW,expected_plan_provenance_sha256="a"*64);self.assertEqual(result["decision"],"approved")
 def test_ai_or_self_approval_denied(self):
  p=packet()
  with self.assertRaises(A.ApprovalDenied):A.validate_decision(packet=p,principal=principal(is_ai=True),submission=decision(p),now=NOW,expected_plan_provenance_sha256="a"*64)
  with self.assertRaises(A.ApprovalDenied):A.validate_decision(packet=p,principal=principal(subject="desk-1"),submission=decision(p),now=NOW,expected_plan_provenance_sha256="a"*64)
 def test_expired_packet_denied(self):
  p=packet()
  with self.assertRaises(A.ApprovalDenied):A.validate_decision(packet=p,principal=principal(),submission=decision(p),now=NOW+dt.timedelta(minutes=16),expected_plan_provenance_sha256="a"*64)
 def test_plan_mutation_invalidates_decision(self):
  p=packet()
  with self.assertRaises(A.ApprovalDenied):A.validate_decision(packet=p,principal=principal(),submission=decision(p),now=NOW,expected_plan_provenance_sha256="c"*64)
 def test_conflicting_replay_denied(self):
  p=packet();first=A.validate_decision(packet=p,principal=principal(),submission=decision(p),now=NOW,expected_plan_provenance_sha256="a"*64)
  with self.assertRaises(A.ApprovalConflict):A.validate_decision(packet=p,principal=principal(),submission=decision(p,decision="rejected",reason="No"),now=NOW,expected_plan_provenance_sha256="a"*64,existing_decision_fingerprint=first["decision_fingerprint"])
 def test_only_validated_approval_advances_execution(self):
  p=packet();approved=A.validate_decision(packet=p,principal=principal(),submission=decision(p),now=NOW,expected_plan_provenance_sha256="a"*64);self.assertEqual(A.supervisor_handoff(approved)["phase"],"execution")
if __name__=="__main__":unittest.main()
