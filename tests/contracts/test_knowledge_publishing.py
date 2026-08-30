from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("knowledge_validator",ROOT/"scripts/validate_knowledge_publishing.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);K=V.module();AUTHOR=K.Actor("author-1","tenant-1",frozenset({"knowledge_author"}),True);APPROVER=K.Actor("approver-1","tenant-1",frozenset({"knowledge_approver"}),True);MIN={"grounding":.9,"safety":.9,"clarity":.85}
def candidate(**changes):
 content=("Restore Outlook connectivity","Outlook disconnected","Refresh scoped session");values=dict(candidate_id="kc1",tenant_id="tenant-1",author_id="author-1",title=content[0],symptoms=(content[1],),resolution_steps=(content[2],),evidence_ids=("ev1",),source_closure_sha256="a"*64,quality_scores={"grounding":.95,"safety":.96,"clarity":.9},duplicate_of=None,content_sha256=K._digest(content));values.update(changes);return K.Candidate(**values)
class KnowledgePublishingTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_PII_is_denied(self):
  with self.assertRaises(K.KnowledgeDenied):K.KnowledgeStore().submit(AUTHOR,candidate(title="Contact user@example.com"))
 def test_provenance_is_required(self):
  with self.assertRaises(K.KnowledgeDenied):K.KnowledgeStore().submit(AUTHOR,candidate(evidence_ids=()))
 def test_author_cannot_self_approve(self):
  store=K.KnowledgeStore();store.submit(AUTHOR,candidate())
  with self.assertRaises(K.KnowledgeDenied):store.publish(K.Actor("author-1","tenant-1",frozenset({"knowledge_approver"}),True),"kc1",MIN)
 def test_duplicate_cannot_publish(self):
  store=K.KnowledgeStore();store.submit(AUTHOR,candidate(duplicate_of="kc0"))
  with self.assertRaises(K.KnowledgeDenied):store.publish(APPROVER,"kc1",MIN)
 def test_quality_gate_fails_closed(self):
  store=K.KnowledgeStore();store.submit(AUTHOR,candidate(quality_scores={"grounding":.5,"safety":.96,"clarity":.9}))
  with self.assertRaises(K.KnowledgeDenied):store.publish(APPROVER,"kc1",MIN)
 def test_publish_versions_and_refreshes_index(self):
  store=K.KnowledgeStore();store.submit(AUTHOR,candidate());version=store.publish(APPROVER,"kc1",MIN);self.assertEqual(version.version,1);self.assertEqual(len(version.index_refresh_sha256),64)
 def test_retirement_creates_immutable_version(self):
  store=K.KnowledgeStore();store.submit(AUTHOR,candidate());store.publish(APPROVER,"kc1",MIN);self.assertEqual(store.retire(APPROVER,"kc1").status,"retired");self.assertEqual(len(store.rows["kc1"].versions),2)
 def test_rollback_targets_published_version(self):
  store=K.KnowledgeStore();store.submit(AUTHOR,candidate());store.publish(APPROVER,"kc1",MIN);store.retire(APPROVER,"kc1");version=store.rollback(APPROVER,"kc1",1);self.assertEqual(version.status,"rolled_back")
if __name__=="__main__":unittest.main()
