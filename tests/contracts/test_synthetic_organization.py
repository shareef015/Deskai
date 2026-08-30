from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("organization_validator", ROOT / "scripts/validate_synthetic_organization.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/synthetic-organization-policy.json").read_text())

class SyntheticOrganizationTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_fixture_is_synthetic_only(self): self.assertTrue(POLICY["synthetic_only"])
    def test_replay_is_deterministic(self): self.assertTrue(POLICY["requirements"]["replay_produces_identical_bytes"])
    def test_all_relationships_are_tenant_scoped(self): self.assertTrue(POLICY["requirements"]["all_relationships_tenant_scoped"])
    def test_reset_cannot_touch_production(self): self.assertTrue(POLICY["reset"]["production_tenants_immutable"])
