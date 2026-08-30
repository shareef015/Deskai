from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("quality_validator", ROOT / "scripts/validate_quality_gates.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/engineering-quality-policy.json").read_text())


class QualityGateTests(unittest.TestCase):
    def test_quality_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_all_required_ci_jobs_exist(self):
        self.assertEqual(len(POLICY["ci"]["required_jobs"]), 5)

    def test_ci_is_required_on_changes(self):
        self.assertTrue(POLICY["ci"]["pull_request_required"])
        self.assertTrue(POLICY["ci"]["default_branch_required"])

    def test_security_scanners_are_mandatory(self):
        self.assertEqual(POLICY["security"]["secret_scanner"], "gitleaks")
        self.assertTrue(POLICY["security"]["dependency_review"])

    def test_silent_bypasses_are_forbidden(self):
        self.assertFalse(POLICY["exceptions"]["silent_bypass_allowed"])
        self.assertTrue(POLICY["exceptions"]["expiry_required"])
