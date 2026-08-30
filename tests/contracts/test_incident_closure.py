from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("closure_validator",ROOT/"scripts/validate_incident_closure.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module();ACTOR=C.Actor("engineer-1","tenant-1",frozenset({"service_desk_engineer"}),True)
def request(**changes):
 values=dict(closure_id="cl1",tenant_id="tenant-1",incident_id="i1",checkpoint_id="cp1",actor_id="engineer-1",technical_checks={"outlook_connect":True,"regression":True},employee_confirmation="fixed",resolution_summary="Outlook connectivity restored",evidence_ids=("ev1",),resolved_at="2026-08-27T10:20:00Z",sla_due_at="2026-08-27T10:30:00Z",knowledge_candidate_id="kc1");values.update(changes);return C.ClosureRequest(**values)
class IncidentClosureTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_technical_checks_are_required(self):
  with self.assertRaises(C.ClosureDenied):C.ClosureStore().close(ACTOR,request(technical_checks={"outlook_connect":False}))
 def test_employee_fixed_confirmation_is_required(self):
  with self.assertRaises(C.ClosureDenied):C.ClosureStore().close(ACTOR,request(employee_confirmation="not_fixed"))
 def test_summary_and_evidence_are_required(self):
  with self.assertRaises(C.ClosureDenied):C.ClosureStore().close(ACTOR,request(evidence_ids=()))
 def test_closure_is_immutable(self):
  store=C.ClosureStore();store.close(ACTOR,request())
  with self.assertRaises(C.ClosureDenied):store.close(ACTOR,request())
 def test_sla_outcome_is_computed(self):
  self.assertEqual(C.ClosureStore().close(ACTOR,request(resolved_at="2026-08-27T10:31:00Z")).sla_outcome,"breached")
 def test_reopen_requires_reason_and_evidence(self):
  store=C.ClosureStore();store.close(ACTOR,request())
  with self.assertRaises(C.ClosureDenied):store.reopen(ACTOR,"tenant-1","i1","unknown","2026-08-27T10:40:00Z",("ev2",))
  with self.assertRaises(C.ClosureDenied):store.reopen(ACTOR,"tenant-1","i1","regression","2026-08-27T10:40:00Z",())
 def test_reopen_preserves_closure(self):
  store=C.ClosureStore();record=store.close(ACTOR,request());row=store.reopen(ACTOR,"tenant-1","i1","regression","2026-08-27T10:40:00Z",("ev2",));self.assertEqual(row.closure,record)
 def test_audit_export_is_hashed_and_role_scoped(self):
  store=C.ClosureStore();store.close(ACTOR,request());report=store.audit_export(ACTOR,"tenant-1","i1");self.assertEqual(len(report["audit_sha256"]),64);self.assertNotIn("engineer-1",str(report))
if __name__=="__main__":unittest.main()
