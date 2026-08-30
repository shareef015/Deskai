from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("dtval",ROOT/"scripts/validate_digital_twin.py");assert SPEC and SPEC.loader;V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);P=json.loads((ROOT/"contracts/digital-twin-policy.json").read_text())
class DigitalTwinTests(unittest.TestCase):
 def test_contract_is_valid(self):self.assertEqual(V.validate(),[])
 def test_optimistic_versioning_required(self):self.assertTrue(P["requirements"]["optimistic_state_version"])
 def test_snapshots_are_content_addressed(self):self.assertTrue(P["requirements"]["snapshots_content_addressed"])
 def test_rollback_is_exact(self):self.assertTrue(P["requirements"]["rollback_restores_exact_previous_value"])
 def test_replay_is_deterministic(self):self.assertTrue(P["requirements"]["same_seed_same_replay_hash"])
