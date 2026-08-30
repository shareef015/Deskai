from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("idempotency_validator", ROOT / "scripts/validate_idempotency.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/idempotency-policy.json").read_text())


class IdempotencyTests(unittest.TestCase):
    def test_idempotency_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_scope_includes_tenant(self): self.assertEqual(POLICY["scope"][0], "tenant_id")
    def test_fingerprint_conflict_is_409(self): self.assertEqual(POLICY["fingerprint"]["same_key_different_fingerprint_status"], 409)
    def test_replay_is_encrypted(self): self.assertTrue(POLICY["replay"]["response_encrypted"])
    def test_only_owner_can_complete(self): self.assertTrue(POLICY["execution"]["only_owner_may_complete"])
