from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("authorization_validator", ROOT / "scripts/validate_authorization.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/authorization-policy.json").read_text())


class AuthorizationTests(unittest.TestCase):
    def test_authorization_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_authorization_denies_by_default(self):
        self.assertEqual(POLICY["decision_model"], "deny_by_default")

    def test_explicit_deny_overrides_allow(self):
        self.assertTrue(POLICY["deny_overrides_allow"])

    def test_token_roles_are_not_authoritative(self):
        self.assertTrue(POLICY["token_roles_are_authorization_hints_only"])

    def test_ai_cannot_receive_human_approval_role(self):
        self.assertIn("ai_identity_cannot_receive_human_approval_role", POLICY["segregation_of_duties"])
