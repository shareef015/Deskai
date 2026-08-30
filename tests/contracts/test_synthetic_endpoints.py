from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("endpoint_validator",ROOT/"scripts/validate_synthetic_endpoints.py"); assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-endpoint-policy.json").read_text())
class SyntheticEndpointTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(),[])
    def test_exactly_ten_endpoints(self): self.assertEqual(POLICY["endpoint_count"],10)
    def test_windows_distribution_is_balanced(self): self.assertEqual(POLICY["os_distribution"],{"windows_10":5,"windows_11":5})
    def test_serials_are_never_stored_raw(self): self.assertTrue(POLICY["requirements"]["raw_serial_numbers_forbidden"])
    def test_reset_replays_initial_state(self): self.assertTrue(POLICY["reset"]["exact_initial_state"])
