from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("outlook_validator",ROOT/"scripts/validate_synthetic_outlook.py"); assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-outlook-environment-policy.json").read_text())
class SyntheticOutlookTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(),[])
    def test_classic_and_new_are_distinct(self): self.assertTrue(POLICY["requirements"]["classic_and_new_clients_distinct"])
    def test_mail_content_is_not_stored(self): self.assertTrue(POLICY["requirements"]["mail_content_not_stored"])
    def test_credentials_and_tokens_are_forbidden(self): self.assertTrue(POLICY["requirements"]["credentials_tokens_and_mfa_secrets_forbidden"])
    def test_faults_are_reversible(self): self.assertTrue(POLICY["requirements"]["faults_explicit_and_reversible"])
