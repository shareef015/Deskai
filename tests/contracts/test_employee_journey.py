from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("journey", ROOT / "scripts" / "validate_employee_journey.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

class EmployeeJourneyTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(MODULE.validate(), [])
    def test_diagnostics_require_consent(self): self.assertIn("unexpired_diagnostic_consent", MODULE.load()["gates"]["endpoint_session"])
    def test_remediation_requires_capability(self): self.assertIn("valid_capability_token", MODULE.load()["gates"]["remediation"])
    def test_resolution_requires_human_confirmation(self): self.assertIn("employee_confirmation_received", MODULE.load()["gates"]["resolved"])
