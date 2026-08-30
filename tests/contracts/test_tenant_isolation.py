from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("tenant_validator", ROOT / "scripts/validate_tenant_isolation.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/tenant-isolation-policy.json").read_text())


class TenantIsolationTests(unittest.TestCase):
    def test_tenant_isolation_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_isolation_is_defense_in_depth(self):
        self.assertGreaterEqual(len(POLICY["isolation_layers"]), 6)

    def test_database_context_is_transaction_local(self):
        self.assertEqual(POLICY["context_lifetime"], "transaction_local")

    def test_runtime_role_cannot_bypass_rls(self):
        role = POLICY["runtime_role"]
        self.assertFalse(role["superuser"])
        self.assertFalse(role["bypass_rls"])
        self.assertFalse(role["owns_tables"])

    def test_llm_cannot_choose_tenant(self):
        boundaries = POLICY["trusted_boundaries"]
        self.assertFalse(boundaries["llm_may_select_tenant"])
        self.assertTrue(boundaries["tenant_id_from_authenticated_claim_required"])
