from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("execution_validator",ROOT/"scripts/validate_execution_verification.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);E=V.module();P=E.Principal("executor-1","tenant-1",frozenset({"executor"}),True)
def token():return E.ExecutionToken("tok-1","tenant-1","inc-1","dev-1","plan-1","a"*64,frozenset({"service.restart"}),"2026-08-27T10:30:00Z")
def action(rollback="service.restore"):return E.ActionSpec("act-1","service.restart","b"*64,rollback,"verify-1")
class ExecutionVerificationTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_exact_plan_and_capability_are_required(self):
  with self.assertRaises(E.ExecutionDenied):E.ExecutionStore().start(P,"run-1",token(),(action(),),"wrong")
  with self.assertRaises(E.ExecutionDenied):E.ExecutionStore().start(P,"run-1",token(),(E.ActionSpec("a","other","b"*64,None,"v"),),"a"*64)
 def test_token_is_single_use(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(),),"a"*64)
  with self.assertRaises(E.ExecutionDenied):store.start(P,"run-2",token(),(action(),),"a"*64)
 def test_action_result_is_immutable(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(),),"a"*64);result=E.ActionResult("act-1","succeeded","c"*64,"d"*64);store.record(P,"run-1",result)
  with self.assertRaises(E.ExecutionDenied):store.record(P,"run-1",result)
 def test_success_routes_to_verification(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(),),"a"*64);self.assertEqual(store.record(P,"run-1",E.ActionResult("act-1","succeeded","c"*64,"d"*64)),"verifying")
 def test_partial_failure_routes_to_rollback(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(),),"a"*64);self.assertEqual(store.record(P,"run-1",E.ActionResult("act-1","partial","c"*64,"d"*64)),"rolling_back")
 def test_irreversible_failure_routes_to_human(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(None),),"a"*64);self.assertEqual(store.record(P,"run-1",E.ActionResult("act-1","failed","c"*64,None)),"human_recovery")
 def test_failed_rollback_escalates(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(),),"a"*64);store.record(P,"run-1",E.ActionResult("act-1","failed","c"*64,None));self.assertEqual(store.rollback(P,"run-1","act-1",False),"human_recovery")
 def test_verification_requires_checks_and_employee(self):
  store=E.ExecutionStore();store.start(P,"run-1",token(),(action(),),"a"*64);store.record(P,"run-1",E.ActionResult("act-1","succeeded","c"*64,"d"*64))
  with self.assertRaises(E.ExecutionDenied):store.verify(P,"run-1",{},"fixed")
  self.assertEqual(store.verify(P,"run-1",{"verify-1":True},"fixed"),"verified")
if __name__=="__main__":unittest.main()
