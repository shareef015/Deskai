from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("network_validator",ROOT/"scripts/validate_synthetic_network.py"); assert SPEC and SPEC.loader
VALIDATOR=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(VALIDATOR)
POLICY=json.loads((ROOT/"contracts/synthetic-network-policy.json").read_text())
class SyntheticNetworkTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(VALIDATOR.validate(),[])
    def test_private_addresses_only(self): self.assertTrue(POLICY["requirements"]["private_address_space_only"])
    def test_network_secrets_are_forbidden(self): self.assertTrue(POLICY["requirements"]["vpn_has_no_secrets_or_private_keys"] and POLICY["requirements"]["wifi_has_no_pre_shared_keys"])
    def test_faults_are_reversible(self): self.assertTrue(POLICY["requirements"]["faults_are_explicit_and_reversible"])
    def test_reset_clears_faults(self): self.assertTrue(POLICY["reset"]["clear_all_injected_faults"])
