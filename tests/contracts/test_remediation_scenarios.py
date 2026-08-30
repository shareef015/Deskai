from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_remediation_scenarios.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class RemediationScenarioTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/remediation-scenarios.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_every_incident_has_remediation_scenario(self):self.assertEqual(self.data()["scenario_count"],220)
 def test_all_execution_outcomes_are_covered(self):self.assertEqual(len({s["outcome"] for s in self.data()["scenarios"]}),7)
 def test_verified_rollbacks_restore_pre_state(self):self.assertTrue(all(s["rollback_result"]["observed_post_rollback_digest"]==s["final_state"]["pre_state_digest"] for s in self.data()["scenarios"] if s["rollback_result"]["verification_passed"]))
 def test_failed_rollbacks_escalate(self):self.assertTrue(all(s["final_state"]["safe_escalation_required"] for s in self.data()["scenarios"] if s["outcome"]=="partial_rollback_failed"))
if __name__=="__main__":unittest.main()
