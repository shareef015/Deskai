from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "packages/python/deskpilot-core/src"
sys.path.insert(0, str(CORE))
from deskpilot_core.configuration import ConfigurationError, load_configuration  # noqa: E402

SPEC = importlib.util.spec_from_file_location("config_validator", ROOT / "scripts/validate_configuration.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ConfigurationTests(unittest.TestCase):
    def test_contract_and_profiles_are_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_production_is_fail_closed(self):
        profile = ROOT / "config/environments/production.json"
        with self.assertRaises(ConfigurationError):
            load_configuration(profile, {"debug": True})

    def test_unknown_keys_are_rejected(self):
        profile = ROOT / "config/environments/test.json"
        with self.assertRaises(ConfigurationError):
            load_configuration(profile, {"surprise": "value"})

    def test_fingerprint_is_stable_and_contains_no_secret(self):
        profile = ROOT / "config/environments/development.json"
        first = load_configuration(profile)
        second = load_configuration(profile)
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(len(first.fingerprint), 64)


if __name__ == "__main__":
    unittest.main()
