from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("secret_validator", ROOT / "scripts/validate_secrets.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SecretPolicyTests(unittest.TestCase):
    def test_secret_contract_and_repository_are_safe(self):
        self.assertEqual(VALIDATOR.validate(), [])

