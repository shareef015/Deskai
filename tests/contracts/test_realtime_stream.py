from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("stream_validator", ROOT / "scripts/validate_realtime_stream.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/realtime-stream-policy.json").read_text())


class RealtimeStreamTests(unittest.TestCase):
    def test_stream_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_stream_is_authenticated(self): self.assertTrue(POLICY["authentication_required"])
    def test_replay_is_exclusive(self): self.assertTrue(POLICY["replay"]["exclusive_resume"])
    def test_heartbeats_are_bounded(self): self.assertEqual(POLICY["connection"]["heartbeat_seconds"], 15)
    def test_clients_deduplicate_events(self): self.assertTrue(POLICY["backpressure"]["client_deduplicates_by_event_id"])
