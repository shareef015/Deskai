from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("incident_api_validator", ROOT / "scripts/validate_incident_api.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/incident-api-policy.json").read_text())


class IncidentApiTests(unittest.TestCase):
    def test_incident_api_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_tenant_cannot_be_supplied_in_request(self): self.assertEqual(POLICY["tenant_source"], "authenticated_principal_only")
    def test_generic_delete_is_not_supported(self): self.assertFalse(POLICY["delete_supported"])
    def test_updates_require_optimistic_version(self):
        self.assertEqual(POLICY["concurrency"]["update_header"], "If-Match")
        self.assertTrue(POLICY["concurrency"]["atomic_database_predicate_required"])
    def test_lists_use_bounded_keyset_pagination(self):
        self.assertEqual(POLICY["pagination"]["strategy"], "keyset")
        self.assertEqual(POLICY["pagination"]["maximum_limit"], 200)
