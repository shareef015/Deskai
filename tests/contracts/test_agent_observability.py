from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("observability_validator",ROOT/"scripts/validate_agent_observability.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);O=V.module();S=O.TraceScope("trace-1","tenant-1","incident-1","thread-1","corr-1")
def event(existing=(),scope=S,event_type="graph_transition",attrs=None,output=None):return O.append_event(existing=existing,scope=scope,event_type=event_type,timestamp="2026-08-27T10:00:00Z",attributes=attrs or {"from_phase":"intake","to_phase":"diagnosis"},input_fingerprint=None,output_fingerprint=output,audit_event_id="audit-1")
class AgentObservabilityTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_hash_chained_trace_validates(self):
  first=event();second=event((first,),event_type="terminal",attrs={"outcome":"resolved"},output="a"*64);O.validate_trace((first,second))
 def test_cross_scope_append_rejected(self):
  first=event();other=O.TraceScope("trace-2","tenant-2","incident-1","thread-1","corr-1")
  with self.assertRaises(O.TraceError):event((first,),scope=other)
 def test_unknown_attribute_rejected(self):
  with self.assertRaises(O.TraceError):event(attrs={"raw_prompt":"secret"})
 def test_secret_and_email_are_redacted(self):
  item=event(attrs={"route_reason":"token=abc user@example.com"});self.assertIn("[redacted-secret]",item.attributes["route_reason"]);self.assertNotIn("user@example.com",item.attributes["route_reason"])
 def test_decision_requires_output_fingerprint(self):
  with self.assertRaises(O.TraceError):event(event_type="agent_decision",attrs={"decision":"route"})
 def test_tampered_event_is_detected(self):
  first=event();tampered=O.TraceEvent(first.sequence,first.event_id,first.event_type,first.scope,first.timestamp,{"to_phase":"execution"},first.input_fingerprint,first.output_fingerprint,first.audit_event_id,first.previous_event_sha256,first.event_sha256)
  with self.assertRaises(O.TraceError):O.validate_trace((tampered,))
 def test_budget_summary_is_content_free(self):
  first=event(attrs={"tokens":100,"cost_microusd":250,"latency_ms":30});summary=O.summarize_trace((first,));self.assertEqual(summary["total_tokens"],100);self.assertNotIn("attributes",summary)
 def test_audit_ids_are_referenced(self):self.assertEqual(O.summarize_trace((event(),))["audit_event_ids"],("audit-1",))
if __name__=="__main__":unittest.main()
