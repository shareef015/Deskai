from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("actions_validator",ROOT/"scripts/validate_governed_actions.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);G=V.module()
def request(**changes):
 values=dict(request_id="req-1",tenant_id="tenant-1",incident_id="inc-1",actor_id="approver",actor_roles=frozenset({"remediation_approver"}),kind="remediation_decision",fields={"decision":"approve","plan_id":"plan-1"},expected_fingerprint=G.fingerprint("tenant-1","inc-1","remediation_decision"));values.update(changes);return G.ActionRequest(**values)
class GovernedActionTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_typed_action_is_recorded(self):self.assertEqual(G.ActionStore().submit(request()).status,"accepted")
 def test_wrong_role_is_denied(self):
  with self.assertRaises(G.ActionDenied):G.ActionStore().submit(request(actor_roles=frozenset({"employee"})))
 def test_stale_fingerprint_is_denied(self):
  with self.assertRaises(G.ActionDenied):G.ActionStore().submit(request(expected_fingerprint="stale"))
 def test_unknown_field_is_denied(self):
  with self.assertRaises(G.ActionDenied):G.ActionStore().submit(request(fields={"decision":"approve","plan_id":"p","extra":"x"}))
 def test_required_field_is_enforced(self):
  with self.assertRaises(G.ActionDenied):G.ActionStore().submit(request(fields={"decision":"approve"}))
 def test_secret_like_content_is_denied(self):
  with self.assertRaises(G.ActionDenied):G.ActionStore().submit(request(fields={"decision":"approve","plan_id":"p","reason":"password=secret123"}))
 def test_duplicate_submission_is_denied(self):
  store=G.ActionStore();store.submit(request())
  with self.assertRaises(G.ActionDenied):store.submit(request())
 def test_rejection_is_explicitly_recorded(self):self.assertEqual(G.ActionStore().submit(request(fields={"decision":"reject","plan_id":"p","reason":"Revise rollback"})).status,"rejected")
if __name__=="__main__":unittest.main()
