from __future__ import annotations
import datetime as dt,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("memory_validator",ROOT/"scripts/validate_memory_governance.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);M=V.module();NOW=dt.datetime(2026,8,27,11,0,tzinfo=dt.timezone.utc)
def request(**changes):
 values=dict(tenant_id="tenant-1",subject_id="employee-1",incident_id="incident-1",memory_class="working",purpose="active_incident",consent_status="not_required",content_fingerprint="a"*64,source_provenance_sha256="b"*64,sensitivity="internal",encrypted=False,human_curated=False,ttl_days=1);values.update(changes);return M.MemoryRequest(**values)
class MemoryGovernanceTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_working_memory_is_incident_scoped(self):
  record=M.create_record(request(),created_at=NOW);scope=M.RecallScope("tenant-1","employee-1","incident-2","active_incident",frozenset({"working"}));self.assertEqual(M.recall((record,),scope,now=NOW),())
 def test_episodic_requires_consent(self):
  with self.assertRaises(M.MemoryDenied):M.create_record(request(memory_class="episodic",purpose="support_continuity",consent_status="declined",ttl_days=30),created_at=NOW)
 def test_reusable_knowledge_requires_human_curation(self):
  with self.assertRaises(M.MemoryDenied):M.create_record(request(memory_class="reusable_knowledge",purpose="curated_knowledge",incident_id=None,ttl_days=365),created_at=NOW)
 def test_sensitive_memory_requires_encryption(self):
  with self.assertRaises(M.MemoryDenied):M.create_record(request(sensitivity="sensitive"),created_at=NOW)
 def test_expired_memory_not_recalled(self):
  record=M.create_record(request(),created_at=NOW);scope=M.RecallScope("tenant-1","employee-1","incident-1","active_incident",frozenset({"working"}));self.assertEqual(M.recall((record,),scope,now=NOW+dt.timedelta(days=2)),())
 def test_cross_tenant_or_subject_not_recalled(self):
  record=M.create_record(request(),created_at=NOW);scope=M.RecallScope("tenant-2","employee-1","incident-1","active_incident",frozenset({"working"}));self.assertEqual(M.recall((record,),scope,now=NOW),())
 def test_conflicting_durable_memory_requires_human_resolution(self):
  a=M.create_record(request(memory_class="episodic",purpose="support_continuity",consent_status="granted",ttl_days=30),created_at=NOW);b=M.create_record(request(memory_class="episodic",purpose="support_continuity",consent_status="granted",ttl_days=30,content_fingerprint="c"*64),created_at=NOW)
  with self.assertRaises(M.MemoryDenied):M.resolve_conflicts((a,b))
 def test_deletion_creates_auditable_tombstone(self):self.assertEqual(len(M.delete_record(M.create_record(request(),created_at=NOW),deletion_actor_id="privacy-admin",reason="subject request")["tombstone_sha256"]),64)
if __name__=="__main__":unittest.main()
