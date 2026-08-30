from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("release_validator",ROOT/"scripts/validate_ai_release_management.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module();AUTHOR=R.Actor("author","tenant-1",frozenset({"release_author"}),True);APPROVER=R.Actor("approver","tenant-1",frozenset({"release_approver"}),True);MANAGER=R.Actor("manager","tenant-1",frozenset({"release_manager"}),True)
def bundle(bundle_id="b1",**changes):
 values=dict(bundle_id=bundle_id,tenant_id="tenant-1",author_id="author",prompt_version="p1",agent_version="a1",model_profile_version="m1",graph_version="g1",schema_version="s1",evaluation_run_sha256="e"*64,compatibility={"prompt_agent":True,"agent_graph":True,"model_tools":True},bundle_sha256="");values.update(changes);values["bundle_sha256"]=R._digest({**values,"bundle_sha256":""});return R.Bundle(**values)
class AIReleaseManagementTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_incompatible_bundle_is_denied(self):
  with self.assertRaises(R.ReleaseDenied):R.ReleaseStore().register(AUTHOR,bundle(compatibility={"prompt_agent":False}))
 def test_author_cannot_self_approve(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle())
  with self.assertRaises(R.ReleaseDenied):store.approve(R.Actor("author","tenant-1",frozenset({"release_approver"}),True),"b1")
 def test_unapproved_rollout_is_denied(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle())
  with self.assertRaises(R.ReleaseDenied):store.rollout(MANAGER,"b1","staging",10)
 def test_canary_bounds_are_enforced(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle());store.approve(APPROVER,"b1")
  with self.assertRaises(R.ReleaseDenied):store.rollout(MANAGER,"b1","staging",0)
 def test_environment_assignments_are_separate(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle());store.approve(APPROVER,"b1");store.rollout(MANAGER,"b1","synthetic",100);self.assertNotIn(("tenant-1","production"),store.deployments)
 def test_full_rollout_activates_bundle(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle());store.approve(APPROVER,"b1");deployment=store.rollout(MANAGER,"b1","staging",100);self.assertEqual(deployment.active_bundle_id,"b1")
 def test_rollback_requires_approved_target(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle());store.approve(APPROVER,"b1");store.rollout(MANAGER,"b1","staging",100)
  with self.assertRaises(R.ReleaseDenied):store.rollback(MANAGER,"tenant-1","staging","unknown")
 def test_emergency_freeze_denies_rollout(self):
  store=R.ReleaseStore();store.register(AUTHOR,bundle());store.approve(APPROVER,"b1");controller=R.Actor("controller","tenant-1",frozenset({"emergency_controller"}),True);store.freeze(controller,"tenant-1","production")
  with self.assertRaises(R.ReleaseDenied):store.rollout(MANAGER,"b1","production",10)
if __name__=="__main__":unittest.main()
