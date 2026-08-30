from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("error_validator", ROOT / "scripts/validate_error_handling.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ErrorPolicyTests(unittest.TestCase):
    def test_error_contract_and_registration_are_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

