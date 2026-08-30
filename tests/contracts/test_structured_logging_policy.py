from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("logging_validator", ROOT / "scripts/validate_structured_logging.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class StructuredLoggingPolicyTests(unittest.TestCase):
    def test_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

