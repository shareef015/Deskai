from __future__ import annotations
import datetime as dt,importlib.util,unittest,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_langgraph_interrupts.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);I=V.module();NOW=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
def uid(n:int)->str:return str(uuid.UUID(int=n))
def request(kind="diagnostic_consent",risk="read_only",requester=None):return I.new_request(kind=kind,tenant_id=uid(1),incident_id=uid(2),thread_id=uid(3),checkpoint_id="cp-1",employee_id="usr-001",device_id="dev-1",purpose="support",capabilities=("endpoint.read",),risk_level=risk,requester_id=requester,action_id="printer.resume_queue" if kind=="remediation_approval" else None,issued_at=NOW,ttl_minutes=10)
def scope(r):return {"tenant_id":r.tenant_id,"incident_id":r.incident_id,"thread_id":r.thread_id,"checkpoint_id":r.checkpoint_id}
class LangGraphInterruptTests(unittest.TestCase):
 def test_contract_is_valid(self):self.assertEqual(V.validate(),[])
 def test_employee_can_grant_scoped_consent(self):
  r=request();p=I.DecisionPrincipal("usr-001",uid(1),frozenset({"employee"}));s=I.DecisionSubmission(r.request_id,r.version,"granted");result=I.validate_resume(request=r,principal=p,submission=s,now=NOW+dt.timedelta(minutes=1),expected_scope=scope(r),assigned_device_ids=frozenset({"dev-1"}));self.assertTrue(result["validated_by_server"])
 def test_expired_cross_tenant_and_ai_resume_fail_closed(self):
  r=request();s=I.DecisionSubmission(r.request_id,r.version,"granted")
  for p,now in [(I.DecisionPrincipal("usr-001",uid(1),frozenset({"employee"})),NOW+dt.timedelta(minutes=11)),(I.DecisionPrincipal("usr-001",uid(9),frozenset({"employee"})),NOW),(I.DecisionPrincipal("svc-ai",uid(1),frozenset({"ai_service"}),True),NOW)]:
   with self.assertRaises(I.ResumeDenied):I.validate_resume(request=r,principal=p,submission=s,now=now,expected_scope=scope(r),assigned_device_ids=frozenset({"dev-1"}))
 def test_requester_cannot_approve_own_medium_risk_action(self):
  r=request("remediation_approval","medium","usr-019");p=I.DecisionPrincipal("usr-019",uid(1),frozenset({"remediation_approver"}));s=I.DecisionSubmission(r.request_id,r.version,"approved")
  with self.assertRaises(I.ResumeDenied):I.validate_resume(request=r,principal=p,submission=s,now=NOW,expected_scope=scope(r),assigned_device_ids=frozenset())
 def test_idempotent_repeat_is_accepted_but_conflict_rejected(self):
  r=request();p=I.DecisionPrincipal("usr-001",uid(1),frozenset({"employee"}));s=I.DecisionSubmission(r.request_id,r.version,"granted");first=I.validate_resume(request=r,principal=p,submission=s,now=NOW,expected_scope=scope(r),assigned_device_ids=frozenset({"dev-1"}));again=I.validate_resume(request=r,principal=p,submission=s,now=NOW,expected_scope=scope(r),assigned_device_ids=frozenset({"dev-1"}),existing_fingerprint=first["decision_fingerprint"]);self.assertTrue(again["idempotent_replay"])
  with self.assertRaises(I.DecisionConflict):I.validate_resume(request=r,principal=p,submission=I.DecisionSubmission(r.request_id,r.version,"declined"),now=NOW,expected_scope=scope(r),assigned_device_ids=frozenset({"dev-1"}),existing_fingerprint=first["decision_fingerprint"])
if __name__=="__main__":unittest.main()
