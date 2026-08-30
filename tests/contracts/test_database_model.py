from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("database_validator", ROOT / "scripts/validate_database_model.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
CONTRACT = json.loads((ROOT / "contracts/database-model.json").read_text())
SCHEMA = (ROOT / "db/schema.sql").read_text()


class DatabaseModelTests(unittest.TestCase):
    def test_database_model_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_postgresql_version_is_pinned(self):
        self.assertEqual(CONTRACT["minimum_version"], "16")

    def test_cross_tenant_references_are_prohibited(self):
        isolation = CONTRACT["tenant_isolation"]
        self.assertTrue(isolation["composite_tenant_foreign_keys_required"])
        self.assertTrue(isolation["cross_tenant_reference_prohibited"])

    def test_authorization_is_not_ai_state(self):
        self.assertIn("authorization_is_separate_from_ai_recommendation", CONTRACT["invariants"])
        self.assertIn("CREATE TABLE approval_decisions", SCHEMA)
        self.assertIn("CREATE TABLE ai_checkpoints", SCHEMA)

    def test_sensitive_payloads_are_references(self):
        controls = CONTRACT["sensitive_data"]
        self.assertTrue(controls["secrets_in_database_prohibited"])
        self.assertTrue(controls["evidence_payloads_use_object_store_references"])
