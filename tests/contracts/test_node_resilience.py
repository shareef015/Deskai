from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("resilience_validator",ROOT/"scripts/validate_node_resilience.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module()
class NodeResilienceTests(unittest.IsolatedAsyncioTestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 async def test_transient_failure_retries_then_succeeds(self):
  calls=0;delays=[]
  async def op():
   nonlocal calls;calls+=1
   if calls<2:raise R.NodeFailure("transient")
   return "ok"
  async def sleep(value):delays.append(value)
  result=await R.execute_node("diagnose",op,now=lambda:1.0,sleep=sleep);self.assertEqual(result.status,"succeeded");self.assertEqual(calls,2);self.assertEqual(delays,[1])
 async def test_authorization_failure_never_retries(self):
  calls=0
  async def op():
   nonlocal calls;calls+=1;raise R.NodeFailure("authorization")
  result=await R.execute_node("execute",op,now=lambda:1.0);self.assertEqual(calls,1);self.assertEqual(result.status,"failed")
 async def test_circuit_opens_at_threshold_and_blocks(self):
  async def op():raise R.NodeFailure("dependency_unavailable")
  state=R.CircuitState("closed",2)
  result=await R.execute_node("retrieve",op,circuit=state,now=lambda:10.0);self.assertEqual(result.circuit.status,"open")
  blocked=await R.execute_node("retrieve",op,circuit=result.circuit,now=lambda:11.0);self.assertEqual(blocked.status,"escalated");self.assertEqual(blocked.events[0].outcome,"circuit_open")
 async def test_half_open_success_closes_circuit(self):
  async def op():return "healthy"
  result=await R.execute_node("retrieve",op,circuit=R.CircuitState("open",3,0.0),now=lambda:31.0);self.assertEqual(result.circuit.status,"closed")
 async def test_partial_mutation_compensates_once(self):
  keys=[]
  async def op():raise R.NodeFailure("permanent",partial_mutation=True)
  async def compensate(key):keys.append(key)
  result=await R.execute_node("remediate",op,now=lambda:1.0,compensate=compensate,idempotency_key="idem-1");self.assertEqual(result.status,"compensated");self.assertEqual(keys,["idem-1"])
 async def test_missing_or_failed_compensation_escalates(self):
  async def op():raise R.NodeFailure("permanent",partial_mutation=True)
  result=await R.execute_node("remediate",op,now=lambda:1.0);self.assertEqual(result.status,"escalated")
 def test_provenance_is_deterministic_for_same_events(self):
  event=(R.AttemptEvent(1,"failure","validation","Node execution failed"),);circuit=R.CircuitState("closed",1);self.assertEqual(R._provenance("intake",event,circuit),R._provenance("intake",event,circuit))
if __name__=="__main__":unittest.main()
