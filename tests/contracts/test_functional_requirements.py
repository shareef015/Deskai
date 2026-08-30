from __future__ import annotations
import importlib.util, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("functional", ROOT / "scripts" / "validate_functional_requirements.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
class FunctionalRequirementTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(MODULE.validate(), [])
    def test_requirements_have_stable_unique_ids(self):
        ids = [x["id"] for x in MODULE.load()["requirements"]]; self.assertEqual(len(ids), len(set(ids)))
    def test_human_handoff_exists(self): self.assertIn("human_handoff", {x["capability"] for x in MODULE.load()["requirements"]})
    def test_use_cases_have_alternatives(self): self.assertTrue(all(x["alternative"] for x in MODULE.load()["use_cases"]))
