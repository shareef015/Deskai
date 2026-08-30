from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("identity_validator",ROOT/"scripts/validate_synthetic_identities.py"); assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-identity-policy.json").read_text())

class SyntheticIdentityTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(),[])
    def test_demo_login_is_never_production(self): self.assertFalse(POLICY["demo_login"]["production_enabled"])
    def test_demo_login_has_no_passwords_or_tokens(self): self.assertFalse(POLICY["demo_login"]["passwords_used"] or POLICY["demo_login"]["issues_real_oidc_tokens"])
    def test_role_claims_are_only_hints(self): self.assertTrue(POLICY["authorization"]["role_claims_are_hints_only"])
    def test_ai_cannot_select_persona(self): self.assertTrue(POLICY["authorization"]["ai_cannot_select_or_elevate_persona"])
