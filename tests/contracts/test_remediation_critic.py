from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("critic_validator",ROOT/"scripts/validate_remediation_critic.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module();ALLOW=frozenset({"flush_dns_cache","restart_spooler","rebuild_outlook_profile"})
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",root_cause="dns_cache_stale",fusion_provenance_sha256="a"*64,plan_id="rmp-1",plan_provenance_sha256="b"*64,plan_author_id="planner-service",approval_requester_id="service-desk-1");values.update(changes);return C.ReviewContext(**values)
def action(**changes):
 values=dict(action_id="flush-dns",capability="flush_dns_cache",risk="low",blast_radius="device",evidence_ids=("e1","e2"),prerequisites=("device_online",),persistent_change=False,pre_state_fields=(),rollback_action=None,required_approver="service_desk_lead",proposed_approver_id="lead-1",verification=("technical_state_verified","target_business_function_works","employee_confirms"),idempotency_key="idem-1");values.update(changes);return C.ReviewAction(**values)
class RemediationCriticTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_plan_passes(self):self.assertEqual(C.review_plan(context(),(action(),),ALLOW).outcome,"pass")
 def test_unsupported_capability_requires_revision(self):self.assertEqual(C.review_plan(context(),(action(capability="unknown"),),ALLOW).outcome,"revise")
 def test_prohibited_capability_escalates(self):self.assertEqual(C.review_plan(context(),(action(capability="disable_firewall"),),ALLOW).outcome,"escalate")
 def test_shared_blast_radius_underclassification_escalates(self):self.assertEqual(C.review_plan(context(),(action(blast_radius="tenant"),),ALLOW).outcome,"escalate")
 def test_persistent_change_without_rollback_requires_revision(self):self.assertEqual(C.review_plan(context(),(action(persistent_change=True),),ALLOW).outcome,"revise")
 def test_missing_evidence_and_verification_require_revision(self):
  result=C.review_plan(context(),(action(evidence_ids=(),verification=()),),ALLOW);self.assertEqual(result.outcome,"revise");self.assertEqual({f.code for f in result.findings},{"missing_evidence_link","verification_gap"})
 def test_approver_conflict_escalates(self):self.assertEqual(C.review_plan(context(),(action(proposed_approver_id="service-desk-1"),),ALLOW).outcome,"escalate")
 def test_only_pass_advances_to_approval(self):
  passed=C.supervisor_handoff(C.review_plan(context(),(action(),),ALLOW));revised=C.supervisor_handoff(C.review_plan(context(),(action(capability="unknown"),),ALLOW));self.assertEqual(passed["phase"],"approval");self.assertEqual(revised["phase"],"remediation_planning")
if __name__=="__main__":unittest.main()
