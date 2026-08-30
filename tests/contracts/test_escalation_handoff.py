from __future__ import annotations
import datetime as dt,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("handoff_validator",ROOT/"scripts/validate_escalation_handoff.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);H=V.module();NOW=dt.datetime(2026,8,27,10,0,tzinfo=dt.timezone.utc)
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",thread_id="thread-1",checkpoint_id="cp-1",reason="network_or_site_outage",severity="high",business_impact="Ten employees cannot reach Outlook.",current_owner_team="service_desk",visited_teams=("service_desk",),handoff_hops=1,evidence_ids=("ev-1","ev-2"),latest_provenance_sha256="a"*64);values.update(changes);return H.EscalationContext(**values)
def principal(**changes):
 values=dict(subject="net-1",tenant_id="tenant-1",roles=frozenset({"network_engineer"}),authenticated=True,team="network_operations");values.update(changes);return H.HandoffPrincipal(**values)
class EscalationHandoffTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_reason_routes_to_deterministic_owner(self):self.assertEqual(H.create_handoff(context(),created_at=NOW).owner_team,"network_operations")
 def test_sla_deadline_reflects_severity(self):
  packet=H.create_handoff(context(),created_at=NOW);self.assertEqual(packet.acknowledge_by,"2026-08-27T10:15:00Z")
 def test_circular_or_excessive_hops_denied(self):
  with self.assertRaises(H.HandoffDenied):H.create_handoff(context(visited_teams=("service_desk","network_operations")),created_at=NOW)
  with self.assertRaises(H.HandoffDenied):H.create_handoff(context(handoff_hops=3),created_at=NOW)
 def test_sensitive_impact_is_redacted(self):self.assertIn("[redacted-secret]",H.create_handoff(context(business_impact="token=abc outage"),created_at=NOW).business_impact)
 def test_wrong_team_cannot_acknowledge(self):
  packet=H.create_handoff(context(),created_at=NOW);action=H.HumanAction(packet.handoff_id,"acknowledged","Taking ownership.",())
  with self.assertRaises(H.HandoffDenied):H.validate_human_action(packet,principal(team="service_desk"),action)
 def test_human_resolution_requires_evidence(self):
  packet=H.create_handoff(context(),created_at=NOW);action=H.HumanAction(packet.handoff_id,"resolved_by_human","Provider route restored.",())
  with self.assertRaises(H.HandoffDenied):H.validate_human_action(packet,principal(),action)
 def test_human_resolution_returns_to_verification(self):
  packet=H.create_handoff(context(),created_at=NOW);action=H.HumanAction(packet.handoff_id,"resolved_by_human","Provider route restored.",( "ev-new",));self.assertEqual(H.validate_human_action(packet,principal(),action)["phase"],"verification")
 def test_circular_transfer_denied(self):
  packet=H.create_handoff(context(),created_at=NOW);action=H.HumanAction(packet.handoff_id,"transferred","Wrong owner.",(),"service_desk")
  with self.assertRaises(H.HandoffDenied):H.validate_human_action(packet,principal(),action)
if __name__=="__main__":unittest.main()
