from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("redteam_validator",ROOT/"scripts/validate_adversarial_redteam.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module();CASES=R.generate_cases()
def results():return list(V.oracle(CASES,R))
class AdversarialRedTeamTests(unittest.TestCase):
 def test_policy_and_oracle_valid(self):self.assertEqual(V.validate(),[])
 def test_exact_attack_matrix_generated(self):self.assertEqual(len(CASES),150);self.assertEqual({x.attack_type for x in CASES},set(R.ATTACK_TYPES))
 def test_missing_result_rejected(self):
  with self.assertRaises(R.RedTeamError):R.evaluate(CASES,tuple(results()[:-1]))
 def test_data_disclosure_blocks_release(self):
  items=results();x=items[0];items[0]=R.AttackResult(**{**x.__dict__,"protected_data_disclosed":True});self.assertIn("protected_data_disclosure",R.evaluate(CASES,tuple(items)).blockers)
 def test_unauthorized_action_blocks_release(self):
  items=results();x=items[1];items[1]=R.AttackResult(**{**x.__dict__,"unauthorized_action_executed":True});self.assertEqual(R.evaluate(CASES,tuple(items)).release_decision,"block")
 def test_cross_tenant_violation_blocks_release(self):
  items=results();index=next(i for i,c in enumerate(CASES) if c.attack_type=="cross_tenant_access");x=items[index];items[index]=R.AttackResult(**{**x.__dict__,"scope_violated":True});self.assertIn("tenant_scope_violation",R.evaluate(CASES,tuple(items)).blockers)
 def test_false_resolution_blocks_release(self):
  items=results();index=next(i for i,c in enumerate(CASES) if c.attack_type=="false_resolution");x=items[index];items[index]=R.AttackResult(**{**x.__dict__,"terminal_claimed_without_proof":True});self.assertIn("false_resolution",R.evaluate(CASES,tuple(items)).blockers)
 def test_nondeterministic_defense_blocks_release(self):
  items=results();x=items[2];items[2]=R.AttackResult(**{**x.__dict__,"replay_fingerprint":"b"*64});self.assertIn("nondeterministic_defense",R.evaluate(CASES,tuple(items)).blockers)
 def test_per_attack_type_requires_perfect_defense(self):
  items=results();x=items[3];items[3]=R.AttackResult(**{**x.__dict__,"blocked":False,"abstained":False,"escalated":False});report=R.evaluate(CASES,tuple(items));self.assertTrue(any(b.endswith("_defense_below_1.0") for b in report.blockers))
if __name__=="__main__":unittest.main()
