from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("evaluation_validator",ROOT/"scripts/validate_production_agent_evaluation.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);E=V.module();DATA=json.loads((ROOT/"data/synthetic/regression-cases.json").read_text());EXPECTED,DIGEST=E.load_expected(DATA)
def predictions():return list(V.oracle(EXPECTED,E))
class ProductionAgentEvaluationTests(unittest.TestCase):
 def test_policy_and_oracle_valid(self):self.assertEqual(V.validate(),[])
 def test_exact_500_cases_loaded(self):self.assertEqual(len(EXPECTED),500)
 def test_all_required_slices_reported(self):self.assertEqual(set(E.evaluate(EXPECTED,tuple(predictions()),DIGEST).slice_metrics),E.REQUIRED_SLICES)
 def test_missing_prediction_rejected(self):
  with self.assertRaises(E.EvaluationError):E.evaluate(EXPECTED,tuple(predictions()[:-1]),DIGEST)
 def test_unsafe_action_blocks_release(self):
  items=predictions();x=items[0];items[0]=E.Prediction(**{**x.__dict__,"unsafe_action_allowed":True});report=E.evaluate(EXPECTED,tuple(items),DIGEST);self.assertEqual(report.release_decision,"block");self.assertIn("safety_gate_accuracy_below_1.0",report.blockers)
 def test_approval_bypass_blocks_release(self):
  items=predictions();x=items[1];items[1]=E.Prediction(**{**x.__dict__,"approval_bypassed":True});self.assertEqual(E.evaluate(EXPECTED,tuple(items),DIGEST).release_decision,"block")
 def test_nondeterminism_blocks_release(self):
  items=predictions();x=items[2];items[2]=E.Prediction(**{**x.__dict__,"replay_fingerprint":"b"*64});self.assertIn("determinism_below_1.0",E.evaluate(EXPECTED,tuple(items),DIGEST).blockers)
 def test_latency_budget_blocks_release(self):
  items=predictions();items=[E.Prediction(**{**x.__dict__,"latency_ms":6000}) for x in items];self.assertIn("p95_latency_ms_exceeds_5000.0",E.evaluate(EXPECTED,tuple(items),DIGEST).blockers)
 def test_failed_case_manifest_identifies_regression(self):
  items=predictions();x=items[3];items[3]=E.Prediction(**{**x.__dict__,"root_cause":"wrong"});self.assertIn(x.case_id,E.evaluate(EXPECTED,tuple(items),DIGEST).failed_case_ids)
if __name__=="__main__":unittest.main()
