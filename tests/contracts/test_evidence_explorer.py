from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("evidence_validator",ROOT/"scripts/validate_evidence_explorer.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);E=V.module();VIEWER=E.Viewer("operator-1","tenant-1",frozenset({"operator"}),True)
def item(**changes):
 values=dict(evidence_id="ev-1",tenant_id="tenant-1",incident_id="inc-1",kind="network",source="endpoint",summary="DNS succeeds",observed_at="2026-08-27T10:00:00Z",expires_at="2026-08-27T10:30:00Z",digest="",specialist_id="windows-network",supervisor_handoff_id="ho-1",contradiction_group=None,details={"check":"dns.resolve","status":"success"});values.update(changes)
 if "digest" not in changes:values["digest"]=E._digest({**values,"digest":""})
 return E.Evidence(**values)
class EvidenceExplorerTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_tenant_query_is_isolated(self):
  store=E.EvidenceStore();store.add(item());self.assertEqual(len(store.query(VIEWER,"inc-1",now="2026-08-27T10:10:00Z")),1);self.assertEqual(store.query(E.Viewer("x","tenant-2",frozenset({"operator"}),True),"inc-1",now="2026-08-27T10:10:00Z"),())
 def test_digest_mismatch_is_denied(self):
  with self.assertRaises(E.EvidenceDenied):E.EvidenceStore().add(item(digest="bad"))
 def test_unsafe_details_are_denied(self):
  with self.assertRaises(E.EvidenceDenied):E.EvidenceStore().add(item(details={"raw_output":"secret"}))
 def test_unredacted_secret_is_denied(self):
  with self.assertRaises(E.EvidenceDenied):E.EvidenceStore().add(item(summary="password: hunter2"))
 def test_freshness_is_derived(self):
  store=E.EvidenceStore();store.add(item());self.assertEqual(store.query(VIEWER,"inc-1",now="2026-08-27T10:31:00Z")[0]["freshness"],"stale")
 def test_contradiction_filter_preserves_conflicts(self):
  store=E.EvidenceStore();store.add(item(contradiction_group="dns"));self.assertEqual(len(store.query(VIEWER,"inc-1",contradictions_only=True,now="2026-08-27T10:10:00Z")),1)
 def test_export_is_role_scoped_and_tenant_hashed(self):
  store=E.EvidenceStore();store.add(item());report=store.export(VIEWER,"inc-1",("ev-1",),now="2026-08-27T10:10:00Z");self.assertNotEqual(report["tenant_id_sha256"],"tenant-1")
  with self.assertRaises(E.EvidenceDenied):store.export(E.Viewer("employee","tenant-1",frozenset({"employee"}),True),"inc-1",("ev-1",),now="2026-08-27T10:10:00Z")
 def test_evidence_is_immutable(self):
  store=E.EvidenceStore();store.add(item())
  with self.assertRaises(E.EvidenceDenied):store.add(item())
if __name__=="__main__":unittest.main()
