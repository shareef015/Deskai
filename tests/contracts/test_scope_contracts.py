from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_scope", ROOT / "scripts" / "validate_scope.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScopeContractTests(unittest.TestCase):
    def test_authoritative_contracts_are_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_only_windows_10_and_11_are_managed(self) -> None:
        scope = MODULE.load("product-scope.json")
        self.assertEqual(
            set(scope["product"]["managed_endpoint_operating_systems"]),
            {"windows_10", "windows_11"},
        )

    def test_resolution_requires_technical_and_user_confirmation(self) -> None:
        scope = MODULE.load("product-scope.json")
        invariant = set(scope["resolution_invariant"])
        self.assertIn("technical_verification_passed", invariant)
        self.assertIn("employee_confirmation_received", invariant)

    def test_llm_cannot_authorize_actions(self) -> None:
        scope = MODULE.load("product-scope.json")
        self.assertIn("authorization_decided_by_llm", scope["prohibited_capabilities"])


if __name__ == "__main__":
    unittest.main()
