from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("validator",ROOT/"scripts/validate_conversation_generator.py");assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)
class ConversationGeneratorTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/"data/synthetic/support-conversations.json").read_text())
 def test_dataset_is_valid(self):self.assertEqual(VALIDATOR.validate(),[])
 def test_all_generated_incidents_are_linked(self):self.assertEqual(len(self.data()["conversations"]),220)
 def test_decline_and_rejection_are_represented(self):
  decisions=[c["decisions"] for c in self.data()["conversations"]];self.assertTrue(any(d["diagnostic_consent"]=="declined" for d in decisions) and any(d["remediation_approval"]=="rejected" for d in decisions))
 def test_declined_consent_prevents_diagnostics(self):self.assertTrue(all(not any(t["state"]=="diagnosing" for t in c["turns"]) for c in self.data()["conversations"] if c["decisions"]["diagnostic_consent"]=="declined"))
 def test_resolved_conversations_have_employee_confirmation(self):self.assertTrue(all(c["decisions"]["employee_confirmation"]=="confirmed" for c in self.data()["conversations"] if c["terminal_state"]=="resolved"))
if __name__=="__main__":unittest.main()
