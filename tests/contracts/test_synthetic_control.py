from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("controlval",ROOT/"scripts/validate_synthetic_control.py");assert SPEC and SPEC.loader;V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);P=json.loads((ROOT/"contracts/synthetic-control-policy.json").read_text())
class SyntheticControlTests(unittest.TestCase):
 def test_contract_is_valid(self):self.assertEqual(V.validate(),[])
 def test_production_is_disabled(self):self.assertFalse(P["requirements"]["production_enabled"])
 def test_only_predefined_scenarios(self):self.assertTrue(P["requirements"]["predefined_scenarios_only"] and P["requirements"]["arbitrary_state_paths_forbidden"])
 def test_ai_cannot_operate_panel(self):self.assertTrue(P["requirements"]["llm_cannot_operate_panel"])
 def test_reset_requires_exact_confirmation(self):self.assertEqual(P["requirements"]["reset_confirmation"],"RESET SYNTHETIC TENANT")
