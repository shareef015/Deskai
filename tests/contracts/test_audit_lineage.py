from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("audit_validator", ROOT / "scripts/validate_audit_lineage.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/audit-evidence-policy.json").read_text())


class AuditLineageTests(unittest.TestCase):
    def test_audit_lineage_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_audit_history_is_append_only(self):
        audit = POLICY["audit"]
        self.assertFalse(audit["update_allowed"])
        self.assertFalse(audit["delete_allowed"])

    def test_hash_chain_is_tenant_scoped(self):
        audit = POLICY["audit"]
        self.assertEqual(audit["scope"], "per_tenant_hash_chain")
        self.assertEqual(audit["integrity_algorithm"], "sha256")

    def test_evidence_lineage_is_append_only(self):
        self.assertTrue(POLICY["evidence_lineage"]["append_only"])

    def test_legal_hold_overrides_expiry(self):
        self.assertTrue(POLICY["retention"]["legal_hold_overrides_expiry"])
