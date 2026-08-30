from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_langgraph_state.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR);S=VALIDATOR.module()
class LangGraphStateTests(unittest.TestCase):
 def test_contract_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_evidence_reducer_is_order_independent_and_idempotent(self):
  a={"evidence_id":"a","tenant_id":"t","incident_id":"i","source":"tool","kind":"state","observed_at":"2026-01-01T00:00:00Z","summary":"a","content_included":False,"digest":"1"};b={**a,"evidence_id":"b","summary":"b","digest":"2"}
  self.assertEqual(S.merge_evidence((a,),(b,)),S.merge_evidence((b,),(a,)));self.assertEqual(S.merge_evidence((a,),(a,)),(a,))
 def test_parallel_reducer_is_associative(self):
  def item(i):return {"message_id":str(i),"sequence":i,"role":"assistant","content":str(i),"created_at":"2026-01-01T00:00:00Z","correlation_id":"c"}
  left=S.merge_messages(S.merge_messages((item(1),),(item(2),)),(item(3),));right=S.merge_messages((item(1),),S.merge_messages((item(2),),(item(3),)));self.assertEqual(left,right)
 def test_histories_and_retries_are_bounded(self):
  messages=tuple({"message_id":str(i),"sequence":i,"role":"assistant","content":"x","created_at":"2026-01-01T00:00:00Z","correlation_id":"c"} for i in range(120));self.assertEqual(len(S.merge_messages((),messages)),100);self.assertEqual(S.merge_retry_counts({}, {"node":99})["node"],3)
 def test_cross_tenant_evidence_and_unapproved_execution_are_rejected(self):
  state=S.new_state({"tenant_id":"t1","incident_id":"i1","thread_id":"th","correlation_id":"c","employee_id":"u","device_id":"d","initial_message":"help"});state["phase"]="execution";state["approval"]={"status":"rejected"};state["evidence"]=({"evidence_id":"e","tenant_id":"t2","incident_id":"i1","source":"tool","kind":"state","observed_at":"2026-01-01T00:00:00Z","summary":"x","content_included":False,"digest":"d"},);errors=S.validate_state(state);self.assertIn("cross-scope evidence",errors);self.assertIn("execution lacks approval",errors)
if __name__=="__main__":unittest.main()
