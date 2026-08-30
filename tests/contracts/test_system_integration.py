from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("integration_validator",ROOT/"scripts/validate_system_integration.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);I=V.module()
class SystemIntegrationTests(unittest.TestCase):
 def test_policy_modules_graph_and_scenarios_valid(self):self.assertEqual(V.validate(),[])
 def test_all_nodes_reachable_and_terminals_closed(self):self.assertEqual(I.validate_graph(),())
 def test_all_four_domains_are_in_readiness_report(self):self.assertEqual(I.build_readiness_report(available_modules=I.REQUIRED_MODULES,scenarios=V.scenarios(I)).decision,"ready")
 def test_consent_bypass_blocks_resolution(self):
  p=V.resolution(I,"bad","outlook","outlook_diagnostics");p=I.ScenarioProof(**{**p.__dict__,"consent_granted":False});self.assertIn("resolution_safety_gate",I.validate_scenario(p))
 def test_approval_bypass_blocks_resolution(self):
  p=V.resolution(I,"bad","printer","print_scan_diagnostics");p=I.ScenarioProof(**{**p.__dict__,"approval_validated":False});self.assertIn("resolution_safety_gate",I.validate_scenario(p))
 def test_employee_confirmation_required(self):
  p=V.resolution(I,"bad","scanner","print_scan_diagnostics");p=I.ScenarioProof(**{**p.__dict__,"employee_confirmed":False});self.assertIn("resolution_safety_gate",I.validate_scenario(p))
 def test_rollback_path_requires_verification(self):
  p=I.ScenarioProof("rollback","windows_network",("greeting","intake","device_resolution","consent","routing","windows_network_diagnostics","evidence_fusion","planning","critic","approval","execution","rollback","verification","employee_confirmation","closure"),True,True,False,True,"resolved");self.assertIn("rollback_not_verified",I.validate_scenario(p))
 def test_missing_module_blocks_readiness(self):
  report=I.build_readiness_report(available_modules=I.REQUIRED_MODULES-frozenset({"mcp_dispatch"}),scenarios=V.scenarios(I));self.assertIn("missing_modules",report.blockers)
 def test_invalid_edge_or_terminal_status_detected(self):
  p=I.ScenarioProof("bad","outlook",("greeting","closure"),True,True,False,True,"resolved");errors=I.validate_scenario(p);self.assertIn("invalid_graph_path",errors);self.assertIn("required_gate_order",errors)
if __name__=="__main__":unittest.main()
