from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("workforce_validator",ROOT/"scripts/validate_synthetic_workforce.py"); assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-workforce-policy.json").read_text())

class SyntheticWorkforceTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(),[])
    def test_workforce_is_synthetic(self): self.assertTrue(POLICY["synthetic_only"])
    def test_replay_is_deterministic(self): self.assertTrue(POLICY["requirements"]["deterministic_replay"])
    def test_skills_do_not_grant_authority(self): self.assertTrue(POLICY["requirements"]["skills_do_not_grant_permissions"])
    def test_assignments_are_tenant_scoped(self): self.assertTrue(POLICY["requirements"]["assignments_are_tenant_scoped"])
