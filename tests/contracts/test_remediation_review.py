from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("review_validator",ROOT/"scripts/validate_remediation_review.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module();REQUESTER=R.Reviewer("engineer-1","tenant-1",frozenset({"service_desk_engineer"}),True);APPROVER=R.Reviewer("approver-1","tenant-1",frozenset({"approver"}),True)
def action(**changes):
 values=dict(action_id="a1",capability="service.restart",risk="medium",depends_on=(),before={"status":"running"},after={"status":"restarted"},rollback_capability="service.restore",verification_id="v1");values.update(changes);return R.Action(**values)
def plan(actions=None,**changes):
 values=dict(plan_id="p1",tenant_id="tenant-1",incident_id="i1",checkpoint_id="cp1",requester_id="engineer-1",created_at="2026-08-27T10:00:00Z",expires_at="2026-08-27T10:30:00Z",actions=tuple(actions or (action(),)),evidence_ids=("ev1",),plan_sha256="");values.update(changes)
 if "plan_sha256" not in changes:values["plan_sha256"]=R._digest({**values,"plan_sha256":""})
 return R.Plan(**values)
def decision(**changes):
 values=dict(decision_id="d1",plan_id="p1",tenant_id="tenant-1",actor_id="approver-1",outcome="approved",reason_code="validated",expected_checkpoint_id="cp1",expected_plan_sha256="",decided_at="2026-08-27T10:10:00Z");values.update(changes);return R.Decision(**values)
class RemediationReviewTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_plan_digest_is_required(self):
  with self.assertRaises(R.ReviewDenied):R.ReviewStore().submit(REQUESTER,plan(plan_sha256="bad"))
 def test_medium_risk_requires_rollback(self):
  with self.assertRaises(R.ReviewDenied):R.ReviewStore().submit(REQUESTER,plan(actions=(action(rollback_capability=None),)))
 def test_dependency_cycle_is_denied(self):
  actions=(action(action_id="a1",depends_on=("a2",)),action(action_id="a2",depends_on=("a1",)))
  with self.assertRaises(R.ReviewDenied):R.ReviewStore().submit(REQUESTER,plan(actions=actions))
 def test_self_approval_is_denied(self):
  store=R.ReviewStore();value=plan();store.submit(REQUESTER,value)
  with self.assertRaises(R.ReviewDenied):store.decide(R.Reviewer("engineer-1","tenant-1",frozenset({"approver"}),True),decision(actor_id="engineer-1",expected_plan_sha256=value.plan_sha256))
 def test_exact_plan_and_checkpoint_are_required(self):
  store=R.ReviewStore();value=plan();store.submit(REQUESTER,value)
  with self.assertRaises(R.ReviewDenied):store.decide(APPROVER,decision(expected_plan_sha256=value.plan_sha256,expected_checkpoint_id="old"))
 def test_decision_is_idempotent(self):
  store=R.ReviewStore();value=plan();store.submit(REQUESTER,value);chosen=decision(expected_plan_sha256=value.plan_sha256);self.assertFalse(store.decide(APPROVER,chosen)["idempotent_replay"]);self.assertTrue(store.decide(APPROVER,chosen)["idempotent_replay"])
 def test_expiry_fails_closed(self):
  store=R.ReviewStore();value=plan();store.submit(REQUESTER,value)
  with self.assertRaises(R.ReviewDenied):store.decide(APPROVER,decision(expected_plan_sha256=value.plan_sha256,decided_at="2026-08-27T10:31:00Z"))
 def test_partial_failure_routes_to_rollback(self):
  store=R.ReviewStore();value=plan();store.submit(REQUESTER,value);store.decide(APPROVER,decision(expected_plan_sha256=value.plan_sha256));self.assertEqual(store.execution_route("p1",{"a1":"failed"}),"rollback")
if __name__=="__main__":unittest.main()
