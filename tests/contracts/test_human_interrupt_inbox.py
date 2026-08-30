from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("interrupt_validator",ROOT/"scripts/validate_human_interrupt_inbox.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);H=V.module()
REQUESTER=H.Actor("engineer-1","tenant-1",frozenset({"service_desk_engineer"}),True);EMPLOYEE=H.Actor("employee-1","tenant-1",frozenset({"employee"}),True);APPROVER=H.Actor("approver-1","tenant-1",frozenset({"approver"}),True)
def request(kind="diagnostic_consent",**changes):
 values=dict(interrupt_id="int-1",tenant_id="tenant-1",incident_id="inc-1",thread_id="thread-1",checkpoint_id="cp-1",kind=kind,requester_id="engineer-1",employee_id="employee-1",created_at="2026-08-27T10:00:00Z",expires_at="2026-08-27T10:30:00Z",review_packet={"title":"Review","summary":"Safe summary","evidence_ids":["ev-1"],"plan_diff":[]});values.update(changes);return H.InterruptRequest(**values)
def decision(outcome="approved",actor="employee-1",**changes):
 values=dict(decision_id="dec-1",interrupt_id="int-1",tenant_id="tenant-1",actor_id=actor,outcome=outcome,reason_code="confirmed",expected_checkpoint_id="cp-1",decided_at="2026-08-27T10:10:00Z");values.update(changes);return H.Decision(**values)
class HumanInterruptInboxTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_employee_sees_only_own_pending_consent(self):
  box=H.InterruptInbox();box.create(REQUESTER,request());self.assertEqual(len(box.list_pending(EMPLOYEE)),1);self.assertEqual(box.list_pending(H.Actor("other","tenant-1",frozenset({"employee"}),True)),())
 def test_cross_tenant_is_denied(self):
  box=H.InterruptInbox()
  with self.assertRaises(H.InterruptDenied):box.create(H.Actor("engineer-1","tenant-2",frozenset({"service_desk_engineer"}),True),request())
 def test_private_review_content_is_denied(self):
  box=H.InterruptInbox()
  with self.assertRaises(H.InterruptDenied):box.create(REQUESTER,request(review_packet={"raw_endpoint_output":"secret"}))
 def test_decision_is_idempotent(self):
  box=H.InterruptInbox();box.create(REQUESTER,request());first=box.decide(EMPLOYEE,decision());second=box.decide(EMPLOYEE,decision());self.assertFalse(first["idempotent_replay"]);self.assertTrue(second["idempotent_replay"])
 def test_checkpoint_mismatch_is_denied(self):
  box=H.InterruptInbox();box.create(REQUESTER,request())
  with self.assertRaises(H.InterruptDenied):box.decide(EMPLOYEE,decision(expected_checkpoint_id="cp-old"))
 def test_requester_cannot_self_approve(self):
  box=H.InterruptInbox();box.create(REQUESTER,request("remediation_approval"))
  with self.assertRaises(H.InterruptDenied):box.decide(REQUESTER,decision(actor="engineer-1"))
  self.assertEqual(box.decide(APPROVER,decision(actor="approver-1"))["status"],"approved")
 def test_expired_interrupt_fails_closed(self):
  box=H.InterruptInbox();box.create(REQUESTER,request())
  with self.assertRaises(H.InterruptDenied):box.decide(EMPLOYEE,decision(decided_at="2026-08-27T10:31:00Z"))
  self.assertEqual(box.records["int-1"].status,"expired")
 def test_events_reconnect_by_cursor_and_hash_actor(self):
  box=H.InterruptInbox();box.create(REQUESTER,request());box.decide(EMPLOYEE,decision());events=box.events_after(EMPLOYEE,1);self.assertEqual(len(events),1);self.assertNotIn("employee-1",str(events))
if __name__=="__main__":unittest.main()
