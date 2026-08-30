from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("ops_validator",ROOT/"scripts/validate_operations_dashboard.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);O=V.module();VIEWER=O.Viewer("operator-1","tenant-1",frozenset({"operator"}),True)
def row(**changes):
 values=dict(incident_id="i1",tenant_id="tenant-1",mode="synthetic",domain="outlook",severity="high",status="diagnosing",owner_type="agent",owner_label="outlook specialist",created_at="2026-08-27T10:00:00Z",sla_due_at="2026-08-27T10:30:00Z",last_progress_at="2026-08-27T10:05:00Z",pending_approval=True,rollback_alert=False);values.update(changes);return O.IncidentRow(**values)
class OperationsDashboardTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_dashboard_role_is_required(self):
  with self.assertRaises(O.DashboardDenied):O.DashboardStore().queue(O.Viewer("employee","tenant-1",frozenset({"employee"}),True),mode="synthetic",now="2026-08-27T10:10:00Z")
 def test_tenant_isolation(self):
  store=O.DashboardStore();store.upsert(row());self.assertEqual(store.queue(O.Viewer("x","tenant-2",frozenset({"operator"}),True),mode="synthetic",now="2026-08-27T10:10:00Z"),())
 def test_live_and_synthetic_are_isolated(self):
  store=O.DashboardStore();store.upsert(row());self.assertEqual(store.queue(VIEWER,mode="live",now="2026-08-27T10:10:00Z"),())
 def test_SLA_and_age_are_derived(self):
  store=O.DashboardStore();store.upsert(row());item=store.queue(VIEWER,mode="synthetic",now="2026-08-27T10:20:00Z")[0];self.assertEqual(item["sla_state"],"at_risk");self.assertEqual(item["age_minutes"],20)
 def test_stalled_run_is_detected(self):
  store=O.DashboardStore();store.upsert(row());self.assertTrue(store.queue(VIEWER,mode="synthetic",now="2026-08-27T10:20:00Z")[0]["stalled"])
 def test_filters_apply(self):
  store=O.DashboardStore();store.upsert(row());self.assertEqual(store.queue(VIEWER,mode="synthetic",domain="printer",now="2026-08-27T10:10:00Z"),())
 def test_summary_counts_backlog_and_alerts(self):
  store=O.DashboardStore();store.upsert(row(rollback_alert=True));summary=store.summary(VIEWER,"synthetic","2026-08-27T10:20:00Z");self.assertEqual(summary["approval_backlog"],1);self.assertEqual(summary["rollback_alerts"],1)
 def test_cursor_returns_only_new_tenant_mode_events(self):
  store=O.DashboardStore();store.upsert(row());store.upsert(row(incident_id="i2"));self.assertEqual(len(store.events_after(VIEWER,"synthetic",1)),1)
if __name__=="__main__":unittest.main()
