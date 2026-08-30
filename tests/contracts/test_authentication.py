from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("auth_validator", ROOT / "scripts/validate_authentication.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/authentication-policy.json").read_text())


class AuthenticationTests(unittest.TestCase):
    def test_authentication_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_legacy_grants_are_disabled(self):
        flow = POLICY["interactive_flow"]
        self.assertFalse(flow["implicit_grant_allowed"])
        self.assertFalse(flow["password_grant_allowed"])

    def test_access_token_claims_are_required(self):
        validation = POLICY["token_validation"]
        self.assertTrue(validation["audience_required"])
        self.assertTrue(validation["expiration_required"])
        self.assertEqual(validation["tenant_claim"], "deskpilot_tenant_id")

    def test_browser_tokens_are_server_side(self):
        session = POLICY["browser_session"]
        self.assertTrue(session["server_side_session"])
        self.assertFalse(session["tokens_exposed_to_browser_javascript"])

    def test_machine_identity_cannot_impersonate_human(self):
        self.assertTrue(POLICY["service_authentication"]["human_impersonation_prohibited"])
