from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("remediation_validator",ROOT/"scripts/validate_remediation_planner.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);P=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",root_cause="dns_cache_stale",fusion_status="root_cause_ready",fusion_provenance_sha256="a"*64,evidence_ids=("e1","e2"),target_business_function="Outlook connectivity");values.update(changes);return P.RootCauseContext(**values)
def action(**changes):
 values=dict(action_id="flush-dns",capability="flush_dns_cache",risk="low",blast_radius="device",prerequisites=("device_online",),expected_effect="clear stale resolver cache",persistent_change=False,pre_state_fields=(),rollback_action=None,required_approver="service_desk_lead",verification=("technical_state_verified","target_business_function_works","employee_confirms"),idempotency_key="idem-1",rank=1);values.update(changes);return P.ActionCandidate(**values)
class RemediationPlannerTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_grounded_root_cause_required(self):
  with self.assertRaises(P.RemediationPlanningError):P.build_plan(context(fusion_status="contradictory_evidence"),(action(),))
 def test_prohibited_action_rejected(self):
  with self.assertRaises(P.RemediationPlanningError):P.build_plan(context(),(action(capability="disable_firewall"),))
 def test_persistent_change_requires_pre_state_and_rollback(self):
  with self.assertRaises(P.RemediationPlanningError):P.build_plan(context(),(action(risk="medium",required_approver="endpoint_administrator",persistent_change=True),))
 def test_end_to_end_verification_required(self):
  with self.assertRaises(P.RemediationPlanningError):P.build_plan(context(),(action(verification=("technical_state_verified",)),))
 def test_shared_service_change_is_high_risk(self):
  with self.assertRaises(P.RemediationPlanningError):P.build_plan(context(),(action(blast_radius="shared_service"),))
 def test_unqualified_approver_rejected(self):
  with self.assertRaises(P.RemediationPlanningError):P.build_plan(context(),(action(required_approver="employee"),))
 def test_lowest_risk_minimal_plan_selected(self):
  high=action(action_id="change-dns",capability="change_dns",risk="high",blast_radius="tenant",persistent_change=True,pre_state_fields=("dns_policy",),rollback_action="restore_dns",required_approver="network_administrator",idempotency_key="idem-2",rank=0)
  plan=P.build_plan(context(),(high,action()));self.assertEqual(tuple(x.action_id for x in plan.actions),("flush-dns",));self.assertEqual(plan.maximum_risk,"low")
 def test_handoff_requires_approval(self):
  handoff=P.supervisor_handoff(P.build_plan(context(),(action(),)));self.assertEqual(handoff["phase"],"approval");self.assertEqual(handoff["remediation_plan_status"],"approval_required")
if __name__=="__main__":unittest.main()
