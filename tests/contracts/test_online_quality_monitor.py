from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("monitor_validator",ROOT/"scripts/validate_online_quality_monitor.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);M=V.module()
BASE=M.ApprovedBaseline("base-1","model-1","prompt-1","a"*64,"b"*64,{"grounding_rate":.97,"recurrence_rate":.05})
def metrics(**changes):
 values={k:0.0 for k in M.CRITICAL_ZERO_TOLERANCE};values.update({"grounding_rate":.97,"verification_success_rate":.95,"appropriate_abstention_rate":.98,"recurrence_rate":.05,"p95_latency_ms":1000.0,"average_cost_microusd":1000.0,"error_rate":.01});values.update(changes);return values
def window(**changes):
 values=dict(window_id="window-1",tenant_id="tenant-1",start_at="2026-08-27T09:00:00Z",end_at="2026-08-27T10:00:00Z",sample_count=100,model_id="model-1",prompt_version="prompt-1",config_fingerprint="a"*64,metrics=metrics(),trace_head_sha256="c"*64);values.update(changes);return M.MonitoringWindow(**values)
class OnlineQualityMonitorTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_healthy_window_continues(self):self.assertEqual(M.evaluate_window(BASE,window()).status,"healthy")
 def test_small_window_rejected(self):
  with self.assertRaises(M.MonitoringError):M.evaluate_window(BASE,window(sample_count=10))
 def test_approval_bypass_freezes_execution(self):
  decision=M.evaluate_window(BASE,window(metrics=metrics(approval_bypass_rate=.01)));self.assertEqual(decision.status,"critical");self.assertEqual(decision.execution_action,"freeze_automated_execution")
 def test_scope_violation_uses_safe_fallback(self):self.assertEqual(M.evaluate_window(BASE,window(metrics=metrics(tenant_scope_violation_rate=.01))).traffic_action,"safe_fallback")
 def test_model_prompt_or_config_drift_is_critical(self):self.assertEqual(M.evaluate_window(BASE,window(model_id="unapproved-model")).status,"critical")
 def test_quality_degradation_increases_review(self):
  decision=M.evaluate_window(BASE,window(metrics=metrics(grounding_rate=.90)));self.assertEqual(decision.status,"degraded");self.assertEqual(decision.traffic_action,"increase_review")
 def test_latency_and_cost_slo_alerts(self):
  decision=M.evaluate_window(BASE,window(metrics=metrics(p95_latency_ms=6000,average_cost_microusd=25000)));self.assertEqual(decision.status,"degraded");self.assertEqual(len([a for a in decision.alerts if a.code.startswith("slo.")]),2)
 def test_supervisor_control_is_deterministic_safe_policy(self):
  decision=M.evaluate_window(BASE,window(metrics=metrics(false_resolution_rate=.01)));controls=M.supervisor_controls(decision);self.assertEqual(controls["safe_fallback_policy"],"deterministic_triage_and_human_review")
if __name__=="__main__":unittest.main()
