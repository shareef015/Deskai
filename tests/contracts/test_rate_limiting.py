from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("rate_validator", ROOT / "scripts/validate_rate_limiting.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/rate-limit-policy.json").read_text())


class RateLimitTests(unittest.TestCase):
    def test_rate_limit_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_three_dimensions_are_enforced(self): self.assertEqual(set(POLICY["dimensions"]), {"tenant", "user", "network"})
    def test_remediation_has_high_cost(self): self.assertGreater(POLICY["costs"]["remediation_dispatch"], POLICY["costs"]["read"])
    def test_partial_consumption_is_prohibited(self): self.assertTrue(POLICY["atomicity"]["partial_bucket_consumption_prohibited"])
    def test_mutations_fail_closed(self): self.assertEqual(POLICY["failure"]["authenticated_mutation"], "fail_closed_503")
