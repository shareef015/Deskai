from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("persistence_validator", ROOT / "scripts/validate_persistence.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/persistence-policy.json").read_text())


class PersistenceTests(unittest.TestCase):
    def test_persistence_boundary_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_tenant_scope_is_mandatory(self):
        scope = POLICY["tenant_scope"]
        self.assertTrue(scope["required_for_tenant_repositories"])
        self.assertTrue(scope["unscoped_lookup_prohibited"])

    def test_unit_of_work_owns_transactions(self):
        transactions = POLICY["transactions"]
        self.assertEqual(transactions["owner"], "unit_of_work")
        self.assertTrue(transactions["rollback_on_exception"])

    def test_external_io_is_outside_transactions(self):
        self.assertTrue(POLICY["transactions"]["external_io_inside_transaction_prohibited"])

    def test_incidents_use_optimistic_concurrency(self):
        self.assertEqual(POLICY["concurrency"]["incident_strategy"], "optimistic_version")
