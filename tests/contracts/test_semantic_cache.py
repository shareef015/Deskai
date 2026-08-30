from __future__ import annotations
import datetime as dt,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("cache_validator",ROOT/"scripts/validate_semantic_cache.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module();NOW=dt.datetime(2026,8,27,11,0,tzinfo=dt.timezone.utc)
def context(**changes):
 values=dict(tenant_id="tenant-1",cache_class="retrieval",task_stage="diagnosis",risk="low",data_class="internal",model_id="model-1",model_release="release-1",prompt_fingerprint="a"*64,config_fingerprint="b"*64,index_fingerprint="c"*64,policy_fingerprint="d"*64,normalized_input_fingerprint="e"*64);values.update(changes);return C.CacheContext(**values)
def entry(ctx=None,**changes):return C.create_entry(ctx or context(),created_at=NOW,ttl_seconds=600,encrypted=changes.get("encrypted",False),grounding_evidence_ids=("ev-1",),grounding_fingerprint="f"*64,value_fingerprint="1"*64,estimated_cost_saved_microusd=1000)
class SemanticCacheTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_retrieval_hit_revalidates_grounding(self):self.assertEqual(C.lookup(context(),entry(),now=NOW,similarity=.95,current_grounding_fingerprint="f"*64).outcome,"hit")
 def test_cross_tenant_entry_misses(self):self.assertEqual(C.lookup(context(tenant_id="tenant-2"),entry(),now=NOW,similarity=.95,current_grounding_fingerprint="f"*64).outcome,"miss")
 def test_high_risk_and_governed_stages_bypass(self):self.assertEqual(C.lookup(context(risk="high"),None,now=NOW,similarity=1,current_grounding_fingerprint=None).outcome,"bypass");self.assertEqual(C.lookup(context(task_stage="approval"),None,now=NOW,similarity=1,current_grounding_fingerprint=None).outcome,"bypass")
 def test_sensitive_cache_requires_encryption(self):
  with self.assertRaises(C.CacheDenied):entry(context(data_class="sensitive"))
 def test_expiry_and_release_change_invalidate(self):self.assertEqual(C.lookup(context(),entry(),now=NOW+dt.timedelta(seconds=601),similarity=.95,current_grounding_fingerprint="f"*64).outcome,"stale");self.assertEqual(C.lookup(context(config_fingerprint="9"*64),entry(),now=NOW,similarity=.95,current_grounding_fingerprint="f"*64).outcome,"miss")
 def test_similarity_threshold_enforced(self):self.assertEqual(C.lookup(context(),entry(),now=NOW,similarity=.80,current_grounding_fingerprint="f"*64).outcome,"miss")
 def test_grounding_change_rejects_hit(self):self.assertEqual(C.lookup(context(),entry(),now=NOW,similarity=.95,current_grounding_fingerprint="0"*64).outcome,"revalidation_failed")
 def test_stampede_lease_requested_only_on_fill(self):self.assertTrue(C.lookup(context(),None,now=NOW,similarity=1,current_grounding_fingerprint=None).requires_fill_lease);self.assertFalse(C.lookup(context(),None,now=NOW,similarity=1,current_grounding_fingerprint=None,fill_lease_held=True).requires_fill_lease)
if __name__=="__main__":unittest.main()
