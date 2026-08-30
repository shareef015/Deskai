from __future__ import annotations
import hashlib,importlib.util,json,unittest,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_graph_replay_migrations.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);M,R=V.modules()
def uid(n):return str(uuid.UUID(int=n))
def legacy():return {"tenant_id":uid(1),"incident_id":uid(2),"thread_id":uid(3),"correlation_id":uid(4),"employee_id":"usr-001","device_id":"dev-1","initial_message":"help","state_version":"0.9.0","stage":"consent","messages":(),"evidence":(),"consent":{"status":"pending"},"approval":{"status":"not_required"},"budgets":{"graph_steps_remaining":80,"tool_calls_remaining":30,"retrieval_rounds_remaining":3},"hypotheses":(),"selected_root_cause":None,"remediation_plan_id":None,"final_status":None}
class GraphReplayMigrationTests(unittest.TestCase):
 def test_contract_is_valid(self):self.assertEqual(V.validate(),[])
 def test_migration_is_pure_and_preserves_scope(self):
  source=legacy();before=json.dumps(source,sort_keys=True);migrated,events=M.default_registry().migrate(source);self.assertEqual(json.dumps(source,sort_keys=True),before);self.assertEqual(migrated["tenant_id"],source["tenant_id"]);self.assertEqual(migrated["phase"],"consent");self.assertEqual(len(events),1)
 def test_unknown_version_fails_closed(self):
  state=legacy();state["state_version"]="0.1.0"
  with self.assertRaises(M.StateMigrationError):M.default_registry().migrate(state)
 def test_replay_creates_new_thread_and_requires_fresh_interrupt(self):
  state=legacy();payload=b"checkpoint";sha=hashlib.sha256(payload).hexdigest();request=R.ReplayRequest("req-1","replay",uid(1),uid(2),uid(3),uid(5),"cp-1",sha,"a"*64);principal=R.ExecutionPrincipal("usr-016",uid(1),frozenset({"service_desk_engineer"}));scope={"tenant_id":uid(1),"incident_id":uid(2),"thread_id":uid(3),"run_id":uid(5),"checkpoint_id":"cp-1","configuration_fingerprint":"a"*64};plan=R.plan_execution(request=request,principal=principal,stored_scope=scope,state=state,serialized_checkpoint=payload);self.assertNotEqual(plan["target_thread_id"],uid(3));self.assertTrue(plan["fresh_human_decision_required"]);self.assertEqual(plan["side_effect_policy"],"recorded_results_only")
 def test_scope_configuration_and_digest_mismatch_fail(self):
  state=legacy();request=R.ReplayRequest("req-1","resume",uid(1),uid(2),uid(3),uid(5),"cp-1","0"*64,"a"*64);principal=R.ExecutionPrincipal("usr-016",uid(1),frozenset({"service_desk_engineer"}));scope={"tenant_id":uid(1),"incident_id":uid(2),"thread_id":uid(3),"run_id":uid(5),"checkpoint_id":"cp-1","configuration_fingerprint":"a"*64}
  with self.assertRaises(R.ReplayDenied):R.plan_execution(request=request,principal=principal,stored_scope=scope,state=state,serialized_checkpoint=b"checkpoint")
if __name__=="__main__":unittest.main()
