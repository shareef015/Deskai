from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("termination_validator",ROOT/"scripts/validate_deterministic_termination.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);T=V.module()
def state(phase="diagnosis",evidence=()):return {"phase":phase,"evidence":evidence,"consent":{"status":"granted"},"approval":{"status":"not_required"},"selected_root_cause":None,"remediation_plan_id":None}
class DeterministicTerminationTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_allowed_transition_continues(self):self.assertEqual(T.guard_transition(state(),"evidence_fusion",T.TerminationTracker()).next_phase,"evidence_fusion")
 def test_invalid_transition_escalates(self):
  decision=T.guard_transition(state(),"resolved",T.TerminationTracker());self.assertTrue(decision.must_terminate);self.assertEqual(decision.reason,"invalid_transition")
 def test_identical_state_cycle_escalates(self):
  tracker=T.TerminationTracker();s=state("clarification")
  T.guard_transition(s,"classification",tracker);T.guard_transition(s,"classification",tracker);decision=T.guard_transition(s,"classification",tracker);self.assertEqual(decision.reason,"state_cycle_detected")
 def test_reasoning_budget_is_bounded(self):
  tracker=T.TerminationTracker(reasoning_turns_used=12);decision=T.guard_transition(state(),"evidence_fusion",tracker,reasoning_turn=True);self.assertEqual(decision.reason,"reasoning_budget_exhausted")
 def test_weak_evidence_abstains_to_escalation(self):
  decision=T.guard_transition(state("evidence_fusion"),"remediation_planning",T.TerminationTracker(),evidence_sufficient=False);self.assertEqual(decision.reason,"insufficient_evidence_abstention")
 def test_terminal_state_is_immutable(self):
  decision=T.guard_transition(state("resolved"),"intake",T.TerminationTracker());self.assertEqual(decision.next_phase,"resolved");self.assertEqual(decision.reason,"terminal_state_immutable")
 def test_termination_proof_is_deterministic_and_updates_state(self):
  tracker=T.TerminationTracker();decision=T.guard_transition(state("confirmation",evidence=({"evidence_id":"e1"},)),"resolved",tracker);proof=T.make_termination_proof(decision,tracker);update=T.terminal_state_update(proof);self.assertEqual(update["final_status"],"resolved");self.assertEqual(len(proof.path_digest),64)
if __name__=="__main__":unittest.main()
