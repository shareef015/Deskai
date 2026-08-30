from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("planning_validator",ROOT/"scripts/validate_planning_governance.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);P=V.module();OBJECTIVES=frozenset({"diagnose_incident"});TOOLS=frozenset({"service_status"});EVIDENCE=frozenset({"ev-1"})
def step(**changes):
 values=dict(step_id="s1",objective="inspect_service",dependencies=(),required_evidence_ids=("ev-1",),tool_id="service_status",risk="read_only",expected_output="typed service state");values.update(changes);return P.PlanStep(**values)
def plan(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",objective_id="diagnose_incident",version=1,parent_plan_sha256=None,replan_count=0,estimated_tokens=1000,estimated_tool_calls=1,estimated_duration_seconds=60,steps=(step(),));values.update(changes);return P.ProposedPlan(**values)
class PlanningGovernanceTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_plan_requires_critic(self):self.assertEqual(P.validate_plan(plan(),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE).outcome,"critic_review")
 def test_unapproved_or_forbidden_objective_denied(self):
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(objective_id="bypass_approval"),approved_objectives=frozenset({"bypass_approval"}),allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
 def test_cycle_is_denied(self):
  steps=(step(step_id="s1",dependencies=("s2",)),step(step_id="s2",dependencies=("s1",)))
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(steps=steps,estimated_tool_calls=2),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
 def test_unapproved_tool_denied(self):
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(steps=(step(tool_id="shell"),)),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
 def test_risky_step_requires_available_evidence(self):
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(steps=(step(risk="medium",required_evidence_ids=()),)),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
 def test_budgets_are_hard_limits(self):
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(estimated_tokens=5000),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
 def test_replan_lineage_and_limit_enforced(self):
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(version=2,replan_count=1,parent_plan_sha256=None),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
  with self.assertRaises(P.PlanDenied):P.validate_plan(plan(version=4,replan_count=3,parent_plan_sha256="a"*64),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
 def test_only_exact_critic_reviewed_plan_advances(self):
  validated=P.validate_plan(plan(),approved_objectives=OBJECTIVES,allowed_tools=TOOLS,available_evidence_ids=EVIDENCE)
  with self.assertRaises(P.PlanDenied):P.accept_critic_review(validated,critic_status="pass",reviewed_plan_sha256="0"*64)
  self.assertEqual(P.accept_critic_review(validated,critic_status="pass",reviewed_plan_sha256=validated.plan_sha256)["planning_status"],"approved_for_orchestration")
if __name__=="__main__":unittest.main()
