from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("migration_validator", ROOT / "scripts/validate_migrations.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/migration-policy.json").read_text())


class MigrationTests(unittest.TestCase):
    def test_migration_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_alembic_is_the_schema_writer(self):
        self.assertEqual(POLICY["tool"], "alembic")
        self.assertTrue(POLICY["single_writer"])

    def test_production_is_forward_only_by_default(self):
        self.assertTrue(POLICY["forward_only_production_default"])
        self.assertIn("automatic_production_downgrade", POLICY["prohibited"])

    def test_rollback_round_trip_is_required(self):
        self.assertIn(
            "upgrade_then_downgrade_then_upgrade_test_required",
            POLICY["deployment_controls"],
        )

    def test_mutable_baseline_is_forbidden(self):
        self.assertIn("mutable_baseline_without_new_revision", POLICY["prohibited"])
