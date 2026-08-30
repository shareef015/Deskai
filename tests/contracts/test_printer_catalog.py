from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_printer_catalog", ROOT / "scripts" / "validate_printer_catalog.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrinterCatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_all_incidents_require_physical_output_confirmation(self) -> None:
        catalog = MODULE.load("printer-support-catalog.json")
        for incident in catalog["incidents"]:
            self.assertIn("physical_output_confirmed", incident["verification"])

    def test_high_risk_changes_require_human_authority(self) -> None:
        catalog = MODULE.load("printer-support-catalog.json")
        for incident in catalog["incidents"]:
            for remediation in incident["remediations"]:
                if remediation["risk"] == "high":
                    self.assertNotIn(remediation["approval"], {"automatic", "llm", "policy"})

    def test_scenarios_cover_windows_10_and_11(self) -> None:
        scenarios = MODULE.load("printer-synthetic-scenarios.json")["scenarios"]
        prefixes = {scenario["device"].split("-")[0] for scenario in scenarios}
        self.assertEqual(prefixes, {"WIN10", "WIN11"})


if __name__ == "__main__":
    unittest.main()
