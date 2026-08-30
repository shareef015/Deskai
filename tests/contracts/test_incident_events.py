from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("event_validator", ROOT / "scripts/validate_incident_events.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/incident-event-policy.json").read_text())


class IncidentEventTests(unittest.TestCase):
    def test_event_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_event_and_outbox_share_transaction(self): self.assertTrue(POLICY["transaction"]["domain_event_and_outbox_same_transaction"])
    def test_delivery_is_at_least_once(self): self.assertEqual(POLICY["outbox"]["delivery"], "at_least_once")
    def test_consumers_must_be_idempotent(self): self.assertTrue(POLICY["outbox"]["consumer_idempotency_required"])
    def test_payload_is_bounded(self): self.assertEqual(POLICY["privacy"]["maximum_payload_bytes"], 65536)
