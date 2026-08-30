from __future__ import annotations
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("priority_engine", ROOT / "services/api/src/deskpilot_api/incidents/priority.py")
assert SPEC and SPEC.loader
ENGINE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ENGINE
SPEC.loader.exec_module(ENGINE)
POLICY = json.loads((ROOT / "contracts/priority-severity-policy.json").read_text())


class PriorityEngineTests(unittest.TestCase):
    def test_matrix_classifies_ordinary_incident(self): self.assertEqual(ENGINE.classify_priority(ENGINE.PrioritySignals(3, 3)).priority, 3)
    def test_security_risk_escalates_to_p1(self): self.assertEqual(ENGINE.classify_priority(ENGINE.PrioritySignals(2, 2, security_or_safety_risk=True)).priority, 1)
    def test_complete_site_outage_escalates_to_p1(self): self.assertEqual(ENGINE.classify_priority(ENGINE.PrioritySignals(2, 2, complete_site_outage=True)).severity, "sev1")
    def test_out_of_range_scores_are_rejected(self):
        with self.assertRaises(ValueError): ENGINE.PrioritySignals(0, 3)
    def test_llm_cannot_override_priority(self): self.assertFalse(POLICY["override"]["llm_may_override"])
