from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("router_validator",ROOT/"scripts/validate_model_router.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);M=V.module()
def profile(mid="model-a",**changes):
 values=dict(model_id=mid,provider_id="provider-1",capabilities=frozenset({"structured_output","reasoning"}),maximum_risk="high",maximum_context_tokens=10000,estimated_cost_microusd=5000,p95_latency_ms=1000,evaluation_score=.99,evaluation_release_id="eval-1",approved=True,data_classes=frozenset({"internal"}),circuit_state="closed");values.update(changes);return M.ModelProfile(**values)
def request(**changes):
 values=dict(tenant_id="tenant-1",task_id="task-1",task_type="evidence_fusion",risk="high",complexity="complex",required_capabilities=frozenset({"reasoning"}),data_class="internal",estimated_input_tokens=1000,maximum_output_tokens=500,latency_slo_ms=3000,remaining_token_budget=5000,remaining_cost_microusd=10000,preferred_model_id="model-a",fallback_allowed=False);values.update(changes);return M.RoutingRequest(**values)
class ModelRouterTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_eligible_preferred_model_selected(self):self.assertEqual(M.route(request(),(profile(),),{}).selected_model_id,"model-a")
 def test_unapproved_or_open_model_not_selected(self):self.assertEqual(M.route(request(),(profile(approved=False),),{}).outcome,"escalate");self.assertEqual(M.route(request(),(profile(circuit_state="open"),),{}).outcome,"escalate")
 def test_high_risk_requires_evaluation_threshold(self):self.assertEqual(M.route(request(),(profile(evaluation_score=.97),),{}).outcome,"escalate")
 def test_token_or_cost_budget_enforced(self):
  with self.assertRaises(M.RoutingDenied):M.route(request(remaining_token_budget=1000),(profile(),),{})
  self.assertEqual(M.route(request(remaining_cost_microusd=1000),(profile(),),{}).outcome,"escalate")
 def test_data_class_and_capability_required(self):self.assertEqual(M.route(request(data_class="restricted"),(profile(),),{}).outcome,"escalate");self.assertEqual(M.route(request(required_capabilities=frozenset({"vision"})),(profile(),),{}).outcome,"escalate")
 def test_no_silent_substitution(self):
  result=M.route(request(),(profile(circuit_state="open"),profile("model-b")),{});self.assertEqual(result.outcome,"escalate");self.assertEqual(result.reason,"preferred_unavailable_no_silent_substitution")
 def test_explicit_fallback_selects_only_governed_model(self):
  result=M.route(request(fallback_allowed=True),(profile(circuit_state="open"),profile("model-b")),{"model-a":("model-b",)});self.assertEqual(result.outcome,"fallback_selected");self.assertEqual(result.selected_model_id,"model-b")
 def test_fallback_hierarchy_is_bounded(self):
  with self.assertRaises(M.RoutingDenied):M.route(request(fallback_allowed=True),(profile(circuit_state="open"),),{"model-a":("b","c","d")})
if __name__=="__main__":unittest.main()
