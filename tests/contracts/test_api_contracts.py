from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("api_contract_validator", ROOT / "scripts/validate_api_contracts.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/api-versioning-policy.json").read_text())

class ApiContractTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_breaking_changes_require_new_major(self): self.assertTrue(POLICY["versioning"]["breaking_changes_require_new_major_prefix"])
    def test_baseline_compatibility_is_required(self): self.assertTrue(POLICY["compatibility"]["baseline_required"])
    def test_generation_is_deterministic(self): self.assertTrue(POLICY["generation"]["deterministic"])
    def test_clients_share_the_canonical_contract(self): self.assertTrue(POLICY["clients"]["generated_from_canonical_artifact"])
