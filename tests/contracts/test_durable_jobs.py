from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("job_validator", ROOT / "scripts/validate_durable_jobs.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/durable-job-policy.json").read_text())


class DurableJobTests(unittest.TestCase):
    def test_job_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(), [])
    def test_enqueue_is_transactional(self): self.assertTrue(POLICY["enqueue"]["same_transaction_as_triggering_state"])
    def test_claim_uses_skip_locked(self): self.assertTrue(POLICY["claim"]["select_for_update_skip_locked"])
    def test_completion_requires_lease(self): self.assertTrue(POLICY["completion"]["matching_lease_token_required"])
    def test_infinite_retry_is_prohibited(self): self.assertTrue(POLICY["dead_letter"]["automatic_infinite_retry_prohibited"])
