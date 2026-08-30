from __future__ import annotations
import importlib.util,json,unittest,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_langgraph_checkpoints.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR);P=VALIDATOR.module()
def uid(n:int)->str:return str(uuid.UUID(int=n))
class LangGraphCheckpointTests(unittest.TestCase):
 def scope(self,tenant:int=1,fingerprint:str="a"*64):return P.ThreadScope(uid(tenant),uid(2),uid(3),fingerprint)
 def test_contract_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_thread_id_is_deterministic_and_tenant_scoped(self):self.assertEqual(self.scope().thread_id,self.scope().thread_id);self.assertNotEqual(self.scope().thread_id,self.scope(tenant=4).thread_id)
 def test_optimistic_concurrency_rejects_stale_head(self):
  head=P.CheckpointHead("cp-1",1,"1.0.0","a"*64)
  with self.assertRaises(P.CheckpointConflict):P.advance_head(head,expected_checkpoint_id="stale",new_checkpoint_id="cp-2",state_version="1.0.0",state_payload=b"{}")
 def test_resume_scope_rejects_tenant_or_configuration_mismatch(self):
  scope=self.scope();stored=scope.__dict__ if hasattr(scope,"__dict__") else {"tenant_id":scope.tenant_id,"incident_id":scope.incident_id,"run_id":scope.run_id,"configuration_fingerprint":"b"*64,"thread_id":scope.thread_id}
  with self.assertRaises(P.CheckpointScopeError):P.assert_resume_scope(scope,stored)
 def test_cleanup_requires_terminal_expired_and_no_hold(self):self.assertTrue(P.cleanup_eligible(status="completed",legal_hold=False,delete_after_reached=True));self.assertFalse(P.cleanup_eligible(status="running",legal_hold=False,delete_after_reached=True));self.assertFalse(P.cleanup_eligible(status="failed",legal_hold=True,delete_after_reached=True))
if __name__=="__main__":unittest.main()
