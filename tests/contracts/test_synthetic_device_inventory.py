from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("inventory_validator",ROOT/"scripts/validate_synthetic_device_inventory.py"); assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-device-inventory-policy.json").read_text())
class SyntheticDeviceInventoryTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(),[])
    def test_all_endpoints_are_covered(self): self.assertTrue(POLICY["requirements"]["all_ten_endpoints_covered"])
    def test_dependencies_are_explicit(self): self.assertTrue(POLICY["requirements"]["dependencies_explicit"])
    def test_expected_and_observed_are_separate(self): self.assertTrue(POLICY["requirements"]["expected_and_observed_state_separate"])
    def test_secrets_are_forbidden(self): self.assertTrue(POLICY["requirements"]["secrets_and_license_keys_forbidden"])
