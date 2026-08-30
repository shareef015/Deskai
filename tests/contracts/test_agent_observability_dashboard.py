from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("obs_validator",ROOT/"scripts/validate_agent_observability_dashboard.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);O=V.module();VIEWER=O.Viewer("ops","tenant-1",frozenset({"operator"}),True)
def span(**changes):
 values=dict(span_id="s1",trace_id="t1",tenant_id="tenant-1",mode="synthetic",incident_id="i1",occurred_at="2026-08-27T10:00:00Z",fields={"node":"intake","agent":"intake","latency_ms":100,"input_tokens":50,"output_tokens":20,"cost_microusd":200,"quality_score":.9,"drift_score":.1,"slo_status":"ok","circuit_state":"closed"});values.update(changes);return O.Span(**values)
class AgentObservabilityDashboardTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_role_is_required(self):
  with self.assertRaises(O.ObservabilityDenied):O.ObservabilityStore().query(O.Viewer("employee","tenant-1",frozenset({"employee"}),True),"synthetic")
 def test_unsafe_trace_field_is_denied(self):
  with self.assertRaises(O.ObservabilityDenied):O.ObservabilityStore().add(span(fields={"raw_prompt":"secret"}))
 def test_negative_metrics_are_denied(self):
  with self.assertRaises(O.ObservabilityDenied):O.ObservabilityStore().add(span(fields={"latency_ms":-1}))
 def test_tenant_isolation(self):
  store=O.ObservabilityStore();store.add(span());self.assertEqual(store.query(O.Viewer("x","tenant-2",frozenset({"operator"}),True),"synthetic"),())
 def test_environment_isolation(self):
  store=O.ObservabilityStore();store.add(span());self.assertEqual(store.query(VIEWER,"live"),())
 def test_agent_filter_applies(self):
  store=O.ObservabilityStore();store.add(span());self.assertEqual(store.query(VIEWER,"synthetic",agent="other"),())
 def test_summary_calculates_cost_quality_and_tokens(self):
  store=O.ObservabilityStore();store.add(span());summary=store.summary(VIEWER,"synthetic");self.assertEqual(summary["tokens"],70);self.assertEqual(summary["cost_microusd"],200);self.assertEqual(summary["average_quality"],.9)
 def test_alerts_include_drift_SLO_and_circuit(self):
  store=O.ObservabilityStore();store.add(span(fields={"latency_ms":1,"drift_score":.3,"slo_status":"breach","circuit_state":"open"}));summary=store.summary(VIEWER,"synthetic");self.assertEqual((summary["drift_alerts"],summary["SLO_alerts"],summary["open_circuits"]),(1,1,1))
if __name__=="__main__":unittest.main()
