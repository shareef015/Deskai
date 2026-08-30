from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("compression_validator",ROOT/"scripts/validate_context_compression.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module()
def state(**changes):
 values={key:() for key in C.PINNED_KEYS};values.update({"tenant_id":"tenant-1","incident_id":"incident-1","thread_id":"thread-1","checkpoint_id":"cp-1","employee_id":"employee-1","device_id":"WIN11-03","phase":"diagnosis","consent":{"status":"granted"},"approval":{"status":"pending"},"selected_root_cause":None,"remediation_plan_id":None,"remediation_plan_provenance_sha256":"","rollback_state":{},"execution_status":"","verification_status":"","budgets":{"tokens":1000},"agent_trace_head_sha256":"a"*64,"state_version":"1.0.0"});values.update(changes);return values
def history():return (C.HistoryItem("i1",1,"message","Employee reports Outlook disconnected.","b"*64,100,1),C.HistoryItem("i2",2,"evidence","DNS lookup timed out.","c"*64,100,1))
class ContextCompressionTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_budget_trigger_reserves_next_step(self):self.assertTrue(C.should_compress(current_tokens=11000,next_step_reserved_tokens=1500));self.assertFalse(C.should_compress(current_tokens=9000,next_step_reserved_tokens=1000))
 def test_compression_pins_governed_state(self):
  result=C.compress(state=state(),history=history(),current_freshness_epoch=1);self.assertEqual(result.pinned_state["consent"],{"status":"granted"});self.assertIn("approval",result.pinned_state)
 def test_missing_pinned_state_rejected(self):
  broken=state();broken.pop("consent")
  with self.assertRaises(C.CompressionError):C.compress(state=broken,history=history(),current_freshness_epoch=1)
 def test_nonsequential_history_rejected(self):
  bad=(C.HistoryItem("i1",2,"message","x","b"*64,1,1),)
  with self.assertRaises(C.CompressionError):C.compress(state=state(),history=bad,current_freshness_epoch=1)
 def test_rehydration_rejects_changed_source(self):
  compressed=C.compress(state=state(),history=history(),current_freshness_epoch=1)
  with self.assertRaises(C.CompressionError):C.validate_rehydration(compressed,live_state=state(),live_source_head_sha256="0"*64,current_freshness_epoch=1)
 def test_rehydration_rejects_stale_summary(self):
  compressed=C.compress(state=state(),history=history(),current_freshness_epoch=1)
  with self.assertRaises(C.CompressionError):C.validate_rehydration(compressed,live_state=state(),live_source_head_sha256=compressed.source_head_sha256,current_freshness_epoch=2)
 def test_rehydration_rejects_pinned_state_change(self):
  compressed=C.compress(state=state(),history=history(),current_freshness_epoch=1)
  with self.assertRaises(C.CompressionError):C.validate_rehydration(compressed,live_state=state(phase="execution"),live_source_head_sha256=compressed.source_head_sha256,current_freshness_epoch=1)
 def test_valid_rehydration_preserves_provenance(self):
  current=state();compressed=C.compress(state=current,history=history(),current_freshness_epoch=1);rehydrated=C.validate_rehydration(compressed,live_state=current,live_source_head_sha256=compressed.source_head_sha256,current_freshness_epoch=1);self.assertEqual(rehydrated["compressed_history_provenance_sha256"],compressed.provenance_sha256)
if __name__=="__main__":unittest.main()
