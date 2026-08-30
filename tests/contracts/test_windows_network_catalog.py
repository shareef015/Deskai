from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_windows_network_catalog",
    ROOT / "scripts" / "validate_windows_network_catalog.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WindowsNetworkCatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_every_incident_verifies_original_business_function(self) -> None:
        catalog = MODULE.load("windows-network-support-catalog.json")
        for incident in catalog["incidents"]:
            self.assertIn("target_business_function_works", incident["verification"])

    def test_firewall_disable_and_credential_collection_are_prohibited(self) -> None:
        catalog = MODULE.load("windows-network-support-catalog.json")
        prohibited = set(catalog["prohibited_actions"])
        self.assertIn("disable_firewall_or_edr_for_testing", prohibited)
        self.assertIn("display_or_export_wifi_password", prohibited)

    def test_scenarios_cover_windows_10_and_11(self) -> None:
        scenarios = MODULE.load("windows-network-synthetic-scenarios.json")["scenarios"]
        prefixes = {scenario["device"].split("-")[0] for scenario in scenarios}
        self.assertEqual(prefixes, {"WIN10", "WIN11"})


if __name__ == "__main__":
    unittest.main()
