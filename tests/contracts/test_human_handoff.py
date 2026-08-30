from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("handoff_validator",ROOT/"scripts/validate_human_handoff.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);H=V.module();REQUESTER=H.Actor("engineer-1","tenant-1",frozenset({"service_desk_engineer"}),True);RESOLVER=H.Actor("resolver-1","tenant-1",frozenset({"resolver"}),True)
def handoff(**changes):
 packet={"summary":"Outlook remains disconnected","reason_code":"recovery_exhausted","severity":"high","evidence_ids":["ev1"],"requested_team":"messaging","verification_ids":["v1"]};values=dict(handoff_id="h1",tenant_id="tenant-1",incident_id="i1",thread_id="t1",checkpoint_id="cp1",requester_id="engineer-1",owner_team="messaging",severity="high",reason_code="recovery_exhausted",created_at="2026-08-27T10:00:00Z",sla_due_at="2026-08-27T10:15:00Z",packet=packet,packet_sha256=H._digest(packet));values.update(changes);return H.Handoff(**values)
class HumanHandoffTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_unsafe_packet_is_denied(self):
  packet={"raw_output":"secret"}
  with self.assertRaises(H.HandoffDenied):H.HandoffStore().create(REQUESTER,handoff(packet=packet,packet_sha256=H._digest(packet)))
 def test_cross_tenant_is_denied(self):
  with self.assertRaises(H.HandoffDenied):H.HandoffStore().create(H.Actor("engineer-1","tenant-2",frozenset({"service_desk_engineer"}),True),handoff())
 def test_sla_state_is_computed(self):
  store=H.HandoffStore();store.create(REQUESTER,handoff());self.assertEqual(store.queue(RESOLVER,"messaging","2026-08-27T10:16:00Z")[0]["sla_state"],"breached")
 def test_acknowledgement_requires_resolver(self):
  store=H.HandoffStore();store.create(REQUESTER,handoff())
  with self.assertRaises(H.HandoffDenied):store.acknowledge(REQUESTER,"h1","2026-08-27T10:05:00Z")
 def test_single_owner_custody(self):
  store=H.HandoffStore();store.create(REQUESTER,handoff());store.acknowledge(RESOLVER,"h1","2026-08-27T10:05:00Z")
  with self.assertRaises(H.HandoffDenied):store.record_change(H.Actor("other","tenant-1",frozenset({"resolver"}),True),"h1","changed","2026-08-27T10:06:00Z")
 def test_human_change_requires_verification(self):
  store=H.HandoffStore();store.create(REQUESTER,handoff());store.acknowledge(RESOLVER,"h1","2026-08-27T10:05:00Z");case=store.record_change(RESOLVER,"h1","profile repaired","2026-08-27T10:06:00Z");self.assertTrue(case.verification_required)
 def test_return_requires_verification_ids(self):
  store=H.HandoffStore();store.create(REQUESTER,handoff());store.acknowledge(RESOLVER,"h1","2026-08-27T10:05:00Z");store.record_change(RESOLVER,"h1","profile repaired","2026-08-27T10:06:00Z")
  with self.assertRaises(H.HandoffDenied):store.return_to_agent(RESOLVER,"h1",(),"2026-08-27T10:07:00Z")
 def test_custody_events_hash_actor(self):
  store=H.HandoffStore();case=store.create(REQUESTER,handoff());self.assertNotEqual(case.events[0].actor_id_sha256,"engineer-1")
if __name__=="__main__":unittest.main()
