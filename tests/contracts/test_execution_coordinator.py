from __future__ import annotations
import datetime as dt,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("execution_validator",ROOT/"scripts/validate_execution_coordinator.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);E=V.module();NOW=dt.datetime(2026,8,27,9,0,tzinfo=dt.timezone.utc);KEY=b"k"*32;ALLOW=frozenset({"flush_dns_cache","restart_service","restore_service_state"})
def plan(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",thread_id="thread-1",checkpoint_id="cp-1",plan_id="rmp-1",plan_provenance_sha256="a"*64,approval_packet_id="packet-1",approval_decision_fingerprint="b"*64,approval_status="approved",action_ids=("flush-dns",),capability_ids=("flush_dns_cache",));values.update(changes);return E.ApprovedPlan(**values)
def dispatch(**changes):
 values=dict(action_id="flush-dns",capability_id="flush_dns_cache",parameters={"cache_scope":"device"},idempotency_key="idem-1",deadline_seconds=30,persistent_change=False,pre_state={},rollback_capability_id=None);values.update(changes);return E.ActionDispatch(**values)
class ExecutionCoordinatorTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_approval_mints_scoped_token(self):self.assertEqual(E.mint_capability_token(plan(),issued_at=NOW,ttl_seconds=300,signing_key=KEY).capability_ids,("flush_dns_cache",))
 def test_unapproved_plan_denied(self):
  with self.assertRaises(E.ExecutionDenied):E.mint_capability_token(plan(approval_status="rejected"),issued_at=NOW,ttl_seconds=300,signing_key=KEY)
 def test_out_of_scope_or_raw_capability_denied(self):
  token=E.mint_capability_token(plan(),issued_at=NOW,ttl_seconds=300,signing_key=KEY)
  with self.assertRaises(E.ExecutionDenied):E.authorize_dispatch(token=token,dispatch=dispatch(capability_id="powershell"),now=NOW,signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="a"*64)
 def test_plan_mutation_or_expired_token_denied(self):
  token=E.mint_capability_token(plan(),issued_at=NOW,ttl_seconds=300,signing_key=KEY)
  with self.assertRaises(E.ExecutionDenied):E.authorize_dispatch(token=token,dispatch=dispatch(),now=NOW,signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="c"*64)
  with self.assertRaises(E.ExecutionDenied):E.authorize_dispatch(token=token,dispatch=dispatch(),now=NOW+dt.timedelta(seconds=301),signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="a"*64)
 def test_raw_command_parameter_denied(self):
  token=E.mint_capability_token(plan(),issued_at=NOW,ttl_seconds=300,signing_key=KEY)
  with self.assertRaises(E.ExecutionDenied):E.authorize_dispatch(token=token,dispatch=dispatch(parameters={"command":"ipconfig /flushdns"}),now=NOW,signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="a"*64)
 def test_persistent_change_requires_pre_state_and_rollback(self):
  token=E.mint_capability_token(plan(),issued_at=NOW,ttl_seconds=300,signing_key=KEY)
  with self.assertRaises(E.ExecutionDenied):E.authorize_dispatch(token=token,dispatch=dispatch(persistent_change=True),now=NOW,signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="a"*64)
 def test_conflicting_idempotent_dispatch_rejected(self):
  token=E.mint_capability_token(plan(),issued_at=NOW,ttl_seconds=300,signing_key=KEY);first=E.authorize_dispatch(token=token,dispatch=dispatch(),now=NOW,signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="a"*64)
  with self.assertRaises(E.ExecutionConflict):E.authorize_dispatch(token=token,dispatch=dispatch(parameters={"cache_scope":"user"}),now=NOW,signing_key=KEY,gateway_allowlist=ALLOW,expected_plan_provenance_sha256="a"*64,existing_dispatch_fingerprint=first["dispatch_fingerprint"])
 def test_result_routes_success_rollback_and_escalation(self):
  self.assertEqual(E.route_result(E.ExecutionResult("a","succeeded",True,True,"a"*64))["phase"],"verification");self.assertEqual(E.route_result(E.ExecutionResult("a","partial",True,True,"b"*64))["execution_recovery_route"],"rollback");self.assertEqual(E.route_result(E.ExecutionResult("a","failed",False,False,"c"*64))["phase"],"escalated")
if __name__=="__main__":unittest.main()
