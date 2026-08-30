from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_outlook_catalog", ROOT / "scripts" / "validate_outlook_catalog.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OutlookCatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_classic_and_new_outlook_are_distinguished(self) -> None:
        catalog = MODULE.load("outlook-support-catalog.json")
        self.assertEqual(set(catalog["clients"]), {"classic_outlook", "new_outlook"})
        self.assertEqual(catalog["clients"]["classic_outlook"]["process"], "outlook.exe")
        self.assertEqual(catalog["clients"]["new_outlook"]["process"], "olk.exe")

    def test_high_risk_actions_are_not_auto_approved(self) -> None:
        catalog = MODULE.load("outlook-support-catalog.json")
        for incident in catalog["incidents"]:
            for remediation in incident["remediations"]:
                if remediation["risk"] == "high":
                    self.assertNotIn(remediation["approval"], {"automatic", "llm"})

    def test_scenarios_cover_both_windows_versions(self) -> None:
        scenarios = MODULE.load("outlook-synthetic-scenarios.json")["scenarios"]
        prefixes = {scenario["device"].split("-")[0] for scenario in scenarios}
        self.assertEqual(prefixes, {"WIN10", "WIN11"})


if __name__ == "__main__":
    unittest.main()
