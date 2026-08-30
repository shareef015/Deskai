from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("asset_validator", ROOT / "scripts/validate_asset_management.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/asset-management-policy.json").read_text())


class AssetManagementTests(unittest.TestCase):
    def test_asset_management_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_only_windows_endpoints_are_supported(self):
        self.assertEqual(set(POLICY["endpoint_operating_systems"]), {"windows_10", "windows_11"})

    def test_assignment_history_is_temporal(self):
        self.assertTrue(POLICY["ownership"]["assignment_history_is_time_bounded"])

    def test_retired_is_terminal(self):
        lifecycle = POLICY["device_lifecycle"]
        self.assertEqual(lifecycle["transitions"]["retired"], [])

    def test_raw_serial_numbers_are_not_stored(self):
        self.assertFalse(POLICY["privacy"]["raw_serial_number_storage_allowed"])
