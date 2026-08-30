from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("runtime_validator",ROOT/"scripts/validate_agent_runtime_api.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module();P=R.Principal("user-1","tenant-1",frozenset({"operator"}),True)
def command(action="start",**changes):
 values=dict(command_id=f"cmd-{action}",tenant_id="tenant-1",incident_id="incident-1",thread_id="thread-1",action=action,expected_checkpoint_id=None,decision_fingerprint=None,synthetic_demo=False);values.update(changes);return R.Command(**values)
class AgentRuntimeAPITests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_authenticated_start_is_idempotent(self):
  store=R.RuntimeStore();first=store.apply(P,command());second=store.apply(P,command());self.assertFalse(first["idempotent_replay"]);self.assertTrue(second["idempotent_replay"])
 def test_duplicate_active_start_denied(self):
  store=R.RuntimeStore();store.apply(P,command())
  with self.assertRaises(R.RuntimeDenied):store.apply(P,command(command_id="cmd-other"))
 def test_cross_tenant_execution_and_stream_denied(self):
  store=R.RuntimeStore()
  with self.assertRaises(R.RuntimeDenied):store.apply(R.Principal("u","tenant-2",frozenset({"operator"}),True),command())
  with self.assertRaises(R.RuntimeDenied):store.stream(R.Principal("u","tenant-2",frozenset({"operator"}),True),"tenant-1","incident-1","thread-1",0)
 def test_resume_requires_checkpoint_and_validated_decision(self):
  store=R.RuntimeStore();started=store.apply(P,command())
  with self.assertRaises(R.RuntimeDenied):store.apply(P,command("resume",expected_checkpoint_id=started["checkpoint_id"]))
  resumed=store.apply(P,command("resume",expected_checkpoint_id=started["checkpoint_id"],decision_fingerprint="a"*64));self.assertNotEqual(resumed["checkpoint_id"],started["checkpoint_id"])
 def test_cancel_makes_terminal_run_immutable(self):
  store=R.RuntimeStore();started=store.apply(P,command());store.apply(P,command("cancel",expected_checkpoint_id=started["checkpoint_id"]))
  with self.assertRaises(R.RuntimeDenied):store.apply(P,command("resume",command_id="cmd-late",expected_checkpoint_id=started["checkpoint_id"],decision_fingerprint="a"*64))
 def test_reconnect_cursor_returns_only_new_events(self):
  store=R.RuntimeStore();started=store.apply(P,command());store.apply(P,command("resume",expected_checkpoint_id=started["checkpoint_id"],decision_fingerprint="a"*64));self.assertEqual(len(store.stream(P,"tenant-1","incident-1","thread-1",1)),1)
 def test_private_event_field_rejected(self):
  store=R.RuntimeStore();execution=R.Execution("tenant-1","incident-1","thread-1","cp-1")
  with self.assertRaises(R.RuntimeDenied):store._event(execution,"graph",{"raw_prompt":"secret"})
 def test_sse_contains_cursor_type_and_safe_data(self):
  store=R.RuntimeStore();store.apply(P,command());encoded=R.encode_sse(store.stream(P,"tenant-1","incident-1","thread-1",0)[0]);self.assertIn("id: 1",encoded);self.assertIn("event: graph",encoded);self.assertNotIn("raw_prompt",encoded)
if __name__=="__main__":unittest.main()
