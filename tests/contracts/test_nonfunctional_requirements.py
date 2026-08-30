from __future__ import annotations
import importlib.util, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("nfr", ROOT / "scripts" / "validate_nonfunctional_requirements.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
class NonFunctionalRequirementTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(MODULE.validate(), [])
    def test_single_node_does_not_claim_high_availability(self): self.assertLess(MODULE.load()["profiles"]["private_ten_device_pilot"]["availability_target_percent"], 99.9)
    def test_budget_exhaustion_preserves_safety(self): self.assertIn("without_bypassing_safety", MODULE.load()["budget"]["hard_limit_behavior"])
    def test_security_invariants_target_zero(self):
        slos = {x["id"]: x["target"] for x in MODULE.load()["slos"]}; self.assertEqual([slos[x] for x in ("SLO-006", "SLO-007", "SLO-008")], [0, 0, 0])
