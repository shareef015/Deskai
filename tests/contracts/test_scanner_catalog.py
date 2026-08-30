from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_scanner_catalog", ROOT / "scripts" / "validate_scanner_catalog.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScannerCatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_every_incident_requires_test_scan_and_employee_confirmation(self) -> None:
        catalog = MODULE.load("scanner-support-catalog.json")
        for incident in catalog["incidents"]:
            self.assertIn("controlled_test_scan_completed", incident["verification"])
            self.assertIn("employee_confirms", incident["verification"])

    def test_employee_documents_are_prohibited_for_diagnostic_scans(self) -> None:
        catalog = MODULE.load("scanner-support-catalog.json")
        self.assertIn("do_not_scan_employee_documents_for_testing", catalog["privacy_rules"])

    def test_scenarios_cover_windows_10_and_11(self) -> None:
        scenarios = MODULE.load("scanner-synthetic-scenarios.json")["scenarios"]
        prefixes = {scenario["device"].split("-")[0] for scenario in scenarios}
        self.assertEqual(prefixes, {"WIN10", "WIN11"})


if __name__ == "__main__":
    unittest.main()
