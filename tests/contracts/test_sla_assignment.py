from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("sla_validator", ROOT / "scripts/validate_sla_assignment.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/sla-assignment-policy.json").read_text())


class SlaAssignmentTests(unittest.TestCase):
    def test_sla_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_p1_uses_continuous_time(self): self.assertEqual(POLICY["targets"]["1"]["calendar"], "continuous")
    def test_acknowledgement_clock_never_pauses(self): self.assertFalse(POLICY["pause"]["acknowledgement_clock_pausable"])
    def test_only_one_active_owner_is_allowed(self): self.assertTrue(POLICY["assignment"]["single_active_owner"])
    def test_escalation_never_remediates(self): self.assertTrue(POLICY["escalation"]["never_auto_close_or_auto_remediate"])
