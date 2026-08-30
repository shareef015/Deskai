from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("conversation_validator",ROOT/"scripts/validate_conversation_stream.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module();ACTOR=C.Actor("employee-1","tenant-1",True)
def command(**changes):
 values=dict(command_id="cmd-1",tenant_id="tenant-1",incident_id="inc-1",thread_id="thread-1",message_id="msg-1",content="Outlook is disconnected",expected_cursor=0);values.update(changes);return C.SendCommand(**values)
class ConversationStreamTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_send_is_idempotent(self):
  store=C.ConversationStore();self.assertFalse(store.send(ACTOR,command())["idempotent_replay"]);self.assertTrue(store.send(ACTOR,command())["idempotent_replay"])
 def test_cross_tenant_is_denied(self):
  with self.assertRaises(C.ConversationDenied):C.ConversationStore().send(C.Actor("employee-1","tenant-2",True),command())
 def test_cursor_mismatch_is_denied(self):
  with self.assertRaises(C.ConversationDenied):C.ConversationStore().send(ACTOR,command(expected_cursor=2))
 def test_secret_is_redacted(self):
  store=C.ConversationStore();store.send(ACTOR,command(content="password: hunter2 Outlook fails"));self.assertNotIn("hunter2",store.rows[("tenant-1","inc-1","thread-1")].events[0].content)
 def test_assistant_deltas_are_typed_and_bounded(self):
  store=C.ConversationStore();row=store.open(ACTOR,"tenant-1","inc-1","thread-1");event=store.assistant_delta(row,"a-1","Checking connection");self.assertEqual(event.event_type,"assistant_delta")
  with self.assertRaises(C.ConversationDenied):store.assistant_delta(row,"a-1","x"*513)
 def test_stop_is_immediate_and_idempotent(self):
  store=C.ConversationStore();first=store.stop(ACTOR,"tenant-1","inc-1","thread-1");second=store.stop(ACTOR,"tenant-1","inc-1","thread-1");self.assertEqual(first,second)
  with self.assertRaises(C.ConversationDenied):store.send(ACTOR,command(expected_cursor=1))
 def test_reconnect_returns_only_new_events(self):
  store=C.ConversationStore();store.send(ACTOR,command());row=store.rows[("tenant-1","inc-1","thread-1")];store.assistant_delta(row,"a-1","Hello");self.assertEqual(len(store.after(ACTOR,"tenant-1","inc-1","thread-1",1)),1)
 def test_history_is_bounded(self):
  store=C.ConversationStore();row=store.open(ACTOR,"tenant-1","inc-1","thread-1")
  for index in range(120):store.assistant_delta(row,f"a-{index}","x")
  self.assertEqual(len(row.events),100)
if __name__=="__main__":unittest.main()
