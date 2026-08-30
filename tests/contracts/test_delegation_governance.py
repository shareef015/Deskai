from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("delegation_validator",ROOT/"scripts/validate_delegation_governance.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);D=V.module()
P=D.ParentAuthority("tenant-1","incident-1","thread-1","supervisor",frozenset({"service_status","dns_resolution"}),frozenset(),10,5000,300,0)
def request(**changes):
 values=dict(child_agent_id="network-specialist",task_type="diagnose_network",objective="collect bounded evidence",input_schema_version="1.0.0",output_schema_version="1.0.0",evidence_ids=("ev-1",),requested_capabilities=frozenset({"dns_resolution"}),requested_authorities=frozenset(),tool_call_budget=4,token_budget=2000,timeout_seconds=60,sibling_count=0);values.update(changes);return D.DelegationRequest(**values)
def result(contract,**changes):
 values=dict(delegation_id=contract.delegation_id,child_agent_id=contract.child_agent_id,status="complete",output_schema_version="1.0.0",evidence_ids=("ev-1",),tool_calls_used=2,tokens_used=1000,elapsed_seconds=30,attempted_authorities=frozenset(),output_fingerprint="a"*64);values.update(changes);return D.ChildResult(**values)
class DelegationGovernanceTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_delegation_is_scoped(self):self.assertEqual(D.authorize(P,request()).tenant_id,"tenant-1")
 def test_capability_expansion_denied(self):
  with self.assertRaises(D.DelegationDenied):D.authorize(P,request(requested_capabilities=frozenset({"execute"})))
 def test_authority_transfer_denied(self):
  with self.assertRaises(D.DelegationDenied):D.authorize(P,request(requested_authorities=frozenset({"approve_remediation"})))
 def test_depth_and_fanout_bounded(self):
  with self.assertRaises(D.DelegationDenied):D.authorize(D.ParentAuthority(**{**P.__dict__,"depth":2}),request())
  with self.assertRaises(D.DelegationDenied):D.authorize(P,request(sibling_count=2))
 def test_child_budget_must_be_parent_subset(self):
  with self.assertRaises(D.DelegationDenied):D.authorize(P,request(tool_call_budget=11))
 def test_child_result_budget_and_authority_validated(self):
  contract=D.authorize(P,request())
  with self.assertRaises(D.DelegationDenied):D.validate_result(contract,result(contract,tokens_used=3000))
  with self.assertRaises(D.DelegationDenied):D.validate_result(contract,result(contract,attempted_authorities=frozenset({"close_incident"})))
 def test_child_cannot_invent_evidence(self):
  contract=D.authorize(P,request())
  with self.assertRaises(D.DelegationDenied):D.validate_result(contract,result(contract,evidence_ids=("ev-new",)))
 def test_cancelled_result_cannot_be_accepted(self):
  contract=D.authorize(P,request())
  with self.assertRaises(D.DelegationDenied):D.validate_result(contract,result(contract),cancelled=True)
if __name__=="__main__":unittest.main()
