from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_consent_approval_scenarios.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class ConsentApprovalScenarioTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/consent-approval-scenarios.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_every_incident_has_authorization_scenario(self):self.assertEqual(self.data()["scenario_count"],220)
 def test_all_fail_closed_outcomes_exist(self):self.assertEqual(len({s["outcome"] for s in self.data()["scenarios"]}),10)
 def test_only_authorized_outcome_can_execute(self):self.assertTrue(all(s["evaluation"]["execution_permitted"]==(s["outcome"]=="authorized") for s in self.data()["scenarios"]))
 def test_ai_auditor_and_self_approval_cannot_execute(self):self.assertTrue(all(not s["evaluation"]["execution_permitted"] for s in self.data()["scenarios"] if s["outcome"] in {"unauthorized_approver","self_approval_denied","ai_authority_denied"}))
if __name__=="__main__":unittest.main()
