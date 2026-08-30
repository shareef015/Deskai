from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("lifecycle_validator", ROOT / "scripts/validate_incident_lifecycle.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/incident-lifecycle-policy.json").read_text())


class IncidentLifecycleTests(unittest.TestCase):
    def test_lifecycle_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_resolved_and_cancelled_are_terminal(self):
        self.assertEqual(POLICY["transitions"]["resolved"], [])
        self.assertEqual(POLICY["transitions"]["cancelled"], [])
    def test_resolution_requires_human_confirmation(self): self.assertIn("employee_confirmation_received", POLICY["guards"]["verifying_to_resolved"])
    def test_status_patch_is_prohibited(self): self.assertTrue(POLICY["persistence"]["direct_status_patch_prohibited"])
    def test_llm_cannot_bypass_guards(self): self.assertFalse(POLICY["authority"]["llm_may_bypass_guard"])
