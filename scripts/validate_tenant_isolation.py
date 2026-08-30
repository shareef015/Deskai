from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/tenant-isolation-policy.json").read_text())
    migration = (ROOT / "services/api/migrations/versions/0003_tenant_row_level_security.py").read_text()
    context = (ROOT / "services/api/src/deskpilot_api/database/tenant_context.py").read_text()
    unit = (ROOT / "services/api/src/deskpilot_api/database/unit_of_work.py").read_text()
    roles = (ROOT / "db/security/database-roles.sql").read_text()
    for token in ("ENABLE ROW LEVEL SECURITY", "FORCE ROW LEVEL SECURITY", "WITH CHECK", "current_setting('app.tenant_id', true)"):
        if token not in migration:
            errors.append(f"RLS control missing: {token}")
    if migration.count('"users"') != 1 or migration.count('"audit_events"') != 1:
        errors.append("tenant table coverage changed")
    for token in ("set_config('app.tenant_id', :tenant_id, true)", "verify_tenant_context"):
        if token not in context:
            errors.append(f"transaction tenant binding missing: {token}")
    if "await bind_tenant_context" not in unit or "await verify_tenant_context" not in unit:
        errors.append("unit of work does not establish verified tenant context")
    for token in ("NOSUPERUSER", "NOBYPASSRLS", "REVOKE CREATE"):
        if token not in roles:
            errors.append(f"runtime role hardening missing: {token}")
    if policy.get("missing_context_behavior") != "deny_all_tenant_rows":
        errors.append("missing tenant context must fail closed")
    if policy.get("trusted_boundaries", {}).get("tenant_id_from_request_body_allowed") is not False:
        errors.append("request body must not select tenant")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("tenant isolation validation passed")
