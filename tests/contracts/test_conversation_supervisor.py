from __future__ import annotations
import importlib.util,unittest
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("conversation_validator",ROOT/"scripts/validate_conversation_supervisor.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);C=V.module()
def context(**changes):
 values=dict(employee_display_name="Sarah",local_time=datetime(2026,8,26,9),turn_count=0,incident_id=None,device_display_name="WIN11-03",intent_summary=None,consent_status="not_requested",locale="en");values.update(changes);return C.ConversationContext(**values)
class ConversationSupervisorTests(unittest.TestCase):
 def test_policy_and_prompt_valid(self):self.assertEqual(V.validate(),[])
 def test_time_aware_greetings(self):self.assertTrue(C.greeting(datetime(2026,1,1,8),"Sarah").startswith("Good morning, Sarah"));self.assertTrue(C.greeting(datetime(2026,1,1,23)).startswith("Hello"))
 def test_clarification_is_accessible_and_bounded(self):
  result=C.continue_conversation(context(),"It does not work",intent_complete=False);self.assertEqual(len(result.questions),2);self.assertIn("details you already provided",result.message)
 def test_diagnostic_consent_is_explicit_and_read_only(self):
  result=C.continue_conversation(context(),"Printer offline",intent_complete=True,needs_diagnostics=True);self.assertEqual(result.outcome,"request_consent");self.assertIn("read-only",result.message);self.assertIn("does not make changes",result.message)
 def test_declined_consent_is_respected(self):
  result=C.continue_conversation(context(consent_status="declined"),"Continue",intent_complete=True,needs_diagnostics=True);self.assertEqual(result.outcome,"handoff");self.assertIn("will not connect",result.message)
 def test_turn_limit_escalates_and_preserves_summary(self):
  result=C.continue_conversation(context(turn_count=40,intent_summary="Printer offline"),"continue",intent_complete=True);self.assertEqual(result.outcome,"escalated");self.assertEqual(result.intent_summary,"Printer offline")
 def test_cancel_stops_actions(self):self.assertEqual(C.continue_conversation(context(),"stop",intent_complete=True).outcome,"cancelled")
 def test_summary_redacts_secret_like_data(self):self.assertNotIn("hunter2",C.safe_summary("password=hunter2 printer issue"));self.assertNotIn("user@example.com",C.safe_summary("Email user@example.com"))
 def test_escalation_never_claims_resolution(self):
  result=C.escalation_response(context(intent_summary="Outlook fails"),"technical_failure");self.assertEqual(result.outcome,"escalated");self.assertNotIn("resolved",result.message.lower())
if __name__=="__main__":unittest.main()
