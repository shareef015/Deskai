from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("supervisor_validator",ROOT/"scripts/validate_master_supervisor.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);S,G=V.modules()
def base():return S.new_state({"tenant_id":"tenant-1","incident_id":"incident-1","thread_id":"thread-1","correlation_id":"correlation-1","employee_id":"employee-1","device_id":"device-1","initial_message":"Printer is offline"})
class MasterSupervisorTests(unittest.TestCase):
 def test_policy_is_valid(self):self.assertEqual(V.validate(),[])
 def test_supported_classification_requests_consent(self):
  state=base();state.update(phase="classification",domain="printer");self.assertEqual(G.route_supervisor(state).next_node,"request_consent")
 def test_unknown_domain_escalates(self):
  state=base();state.update(phase="classification",domain="unknown");self.assertEqual(G.route_supervisor(state).next_node,"escalate")
 def test_diagnostics_without_consent_are_blocked(self):
  state=base();state["phase"]="diagnosis";self.assertEqual(G.route_supervisor(state).reason,"diagnostics_without_valid_consent_blocked")
 def test_execution_requires_capability_token(self):
  state=base();state.update(phase="execution",approval={"status":"approved"});self.assertEqual(G.route_supervisor(state).reason,"capability_token_missing")
 def test_confirmation_always_interrupts(self):
  state=base();state["phase"]="confirmation";self.assertEqual(G.route_supervisor(state).next_node,"employee_confirmation_interrupt")
 def test_route_consumes_one_step_and_records_reason(self):
  state=base();decision=G.route_supervisor(state);update=G.apply_route_provenance(state,decision);self.assertEqual(update["budgets"]["graph_steps_remaining"],79);self.assertEqual(update["graph_version"],"1.0.0")
if __name__=="__main__":unittest.main()
