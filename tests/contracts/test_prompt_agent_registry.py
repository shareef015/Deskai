from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("registry_validator",ROOT/"scripts/validate_prompt_agent_registry.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module()
def prompt():return R.make_prompt(artifact_id="p1",name="intake",version="1.0.0",template="Help {employee} with {symptom}",variables=("employee","symptom"),input_schema_version="1.0.0",output_schema_version="1.0.0",author_id="author")
def agent(p):return R.make_agent(artifact_id="a1",agent_name="intake",version="1.0.0",prompt=p,state_schema_version="1.0.0",input_schema_version="1.0.0",output_schema_version="1.0.0",allowed_tools=(),max_steps=8,max_tool_calls=0,max_tokens=2048,author_id="author")
def approval(aid):return R.Approval(aid,"approver",frozenset({"ai_configuration_approver"}),"approved")
def evaluation():return R.EvaluationEvidence(.95,.9,1.0,.01,"1.0.0","a"*64)
class PromptAgentRegistryTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_prompt_variables_must_match_exactly(self):
  with self.assertRaises(R.RegistryError):R.make_prompt(artifact_id="p",name="x",version="1.0.0",template="Hi {name}",variables=(),input_schema_version="1.0.0",output_schema_version="1.0.0",author_id="a")
 def test_agent_schema_and_budget_compatibility(self):
  p=prompt()
  with self.assertRaises(R.RegistryError):R.make_agent(artifact_id="a",agent_name="x",version="1.0.0",prompt=p,state_schema_version="1.0.0",input_schema_version="2.0.0",output_schema_version="1.0.0",allowed_tools=(),max_steps=1,max_tool_calls=0,max_tokens=1,author_id="a")
 def test_author_cannot_approve(self):
  p=prompt()
  with self.assertRaises(R.RegistryError):R.approve(p,R.Approval("p1","author",frozenset({"ai_configuration_approver"}),"approved"))
 def test_failed_evaluation_blocks_release(self):
  p=prompt();a=agent(p);bad=R.EvaluationEvidence(.5,.9,1.0,.01,"1.0.0","a"*64)
  with self.assertRaises(R.RegistryError):R.create_release(release_id="r1",tenant_id="t1",prompt=p,agent=a,prompt_approval=approval("p1"),agent_approval=approval("a1"),evaluation=bad)
 def test_release_fingerprint_and_deployment_are_deterministic(self):
  p=prompt();a=agent(p);bundle=R.create_release(release_id="r1",tenant_id="t1",prompt=p,agent=a,prompt_approval=approval("p1"),agent_approval=approval("a1"),evaluation=evaluation());self.assertEqual(len(bundle.configuration_fingerprint),64);event=R.deployment_event(bundle,mode="canary",percentage=10,actor_id="operator");self.assertEqual(event["configuration_fingerprint"],bundle.configuration_fingerprint)
 def test_rollback_requires_known_fingerprint(self):
  p=prompt();a=agent(p);bundle=R.create_release(release_id="r1",tenant_id="t1",prompt=p,agent=a,prompt_approval=approval("p1"),agent_approval=approval("a1"),evaluation=evaluation())
  with self.assertRaises(R.RegistryError):R.deployment_event(bundle,mode="rolled_back",percentage=0,actor_id="operator")
if __name__=="__main__":unittest.main()
