from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_personas", ROOT / "scripts" / "validate_personas.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PersonaAuthorityTests(unittest.TestCase):
    def test_contracts_are_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_ai_service_has_no_approval_permission(self) -> None:
        authority = MODULE.load("personas-authority-model.json")
        permissions = set(authority["machine_identities"]["ai_service"])
        self.assertFalse(any("approve" in permission for permission in permissions))

    def test_auditor_is_read_only(self) -> None:
        authority = MODULE.load("personas-authority-model.json")
        auditor = authority["roles"]["auditor"]
        self.assertIn("audit.read", auditor["permissions"])
        self.assertIn("endpoint.execute", auditor["denied"])

    def test_all_personas_are_synthetic_and_roles_are_represented(self) -> None:
        synthetic = MODULE.load("synthetic-personas.json")
        authority = MODULE.load("personas-authority-model.json")
        self.assertTrue(synthetic["synthetic_only"])
        self.assertTrue(set(authority["roles"]).issubset({p["role"] for p in synthetic["personas"]}))


if __name__ == "__main__":
    unittest.main()
