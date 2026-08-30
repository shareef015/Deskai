from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("gate_validator",ROOT/"scripts/validate_evaluation_release_gates.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);G=V.module();ENGINEER=G.Actor("eng","tenant-1",frozenset({"ai_engineer"}),True);APPROVER=G.Actor("approver","tenant-1",frozenset({"release_approver"}),True)
def evaluation(run_id,metrics,**changes):
 values=dict(run_id=run_id,tenant_id="tenant-1",mode="offline",release_id="rel1",dataset_sha256="a"*64,config_sha256="b"*64,metrics=metrics,slices={"outlook":{"safety":metrics.get("safety",0)}},evidence_ids=("ev1",),run_sha256="");values.update(changes);values["run_sha256"]=G._digest({**values,"run_sha256":""});return G.Evaluation(**values)
POLICY=G.GatePolicy({"grounding":.9,"safety":.97},{"grounding":.02,"safety":0},frozenset({"safety"}))
class EvaluationReleaseGateTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_baseline_scope_must_match(self):
  with self.assertRaises(G.GateDenied):G.GateStore().evaluate(ENGINEER,evaluation("b",{"grounding":.95,"safety":.99}),evaluation("c",{"grounding":.95,"safety":.99},mode="online"),POLICY)
 def test_provenance_is_required(self):
  candidate=evaluation("c",{"grounding":.95,"safety":.99});candidate=G.Evaluation(**{**candidate.__dict__,"evidence_ids":()})
  with self.assertRaises(G.GateDenied):G.GateStore().evaluate(ENGINEER,evaluation("b",{"grounding":.95,"safety":.99}),candidate,POLICY)
 def test_threshold_blocker_blocks_release(self):
  gate=G.GateStore().evaluate(ENGINEER,evaluation("b",{"grounding":.95,"safety":.99}),evaluation("c",{"grounding":.95,"safety":.96}),POLICY);self.assertEqual(gate.status,"blocked")
 def test_regression_budget_creates_finding(self):
  gate=G.GateStore().evaluate(ENGINEER,evaluation("b",{"grounding":.96,"safety":.99}),evaluation("c",{"grounding":.93,"safety":.99}),POLICY);self.assertTrue(any(item["class"]=="regression" for item in gate.blockers))
 def test_warning_can_proceed_to_review(self):
  policy=G.GatePolicy({"grounding":.95},{},frozenset());gate=G.GateStore().evaluate(ENGINEER,evaluation("b",{"grounding":.96}),evaluation("c",{"grounding":.94}),policy);self.assertEqual(gate.status,"review")
 def test_blocked_gate_cannot_be_approved(self):
  store=G.GateStore();candidate=evaluation("c",{"grounding":.95,"safety":.96});store.evaluate(ENGINEER,evaluation("b",{"grounding":.95,"safety":.99}),candidate,POLICY)
  with self.assertRaises(G.GateDenied):store.approve(APPROVER,"rel1",candidate.run_sha256)
 def test_exact_run_fingerprint_is_required(self):
  store=G.GateStore();candidate=evaluation("c",{"grounding":.95,"safety":.99});store.evaluate(ENGINEER,evaluation("b",{"grounding":.95,"safety":.99}),candidate,POLICY)
  with self.assertRaises(G.GateDenied):store.approve(APPROVER,"rel1","wrong")
 def test_independent_approval_records_fingerprint(self):
  store=G.GateStore();candidate=evaluation("c",{"grounding":.95,"safety":.99});store.evaluate(ENGINEER,evaluation("b",{"grounding":.95,"safety":.99}),candidate,POLICY);gate=store.approve(APPROVER,"rel1",candidate.run_sha256);self.assertEqual(len(gate.approval_sha256 or ""),64)
if __name__=="__main__":unittest.main()
