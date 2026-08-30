from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deskpilot_api_security.database import DatabaseTenantError, postgres_tenant_context_statement, validate_tenant_uuid


class DatabaseTenantContractTests(unittest.TestCase):
    def test_tenant_context_is_parameterized_and_uuid_validated(self) -> None:
        tenant = "11111111-1111-4111-8111-111111111111"
        self.assertEqual(validate_tenant_uuid(tenant), tenant)
        self.assertIn("$1", postgres_tenant_context_statement())
        self.assertNotIn(tenant, postgres_tenant_context_statement())
        with self.assertRaises(DatabaseTenantError):
            validate_tenant_uuid("tenant-a'; RESET ALL; --")

    def test_rls_migration_enables_and_forces_policies_with_write_checks(self) -> None:
        sql = (ROOT / "migrations" / "0123_tenant_rls.sql").read_text()
        for table in ("incidents", "devices", "audit_events"):
            self.assertIn(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY", sql)
            self.assertIn(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY", sql)
            self.assertIn(f"CREATE POLICY {table}_tenant_isolation ON {table}", sql)
        self.assertGreaterEqual(sql.count("USING (tenant_id = current_setting('app.tenant_id', true)::uuid)"), 3)
        self.assertGreaterEqual(sql.count("WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"), 3)


if __name__ == "__main__":
    unittest.main()
