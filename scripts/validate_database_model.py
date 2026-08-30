from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TABLES = {
    "tenants", "users", "devices", "incidents", "incident_events", "evidence_items",
    "consent_decisions", "approval_decisions", "remediation_plans",
    "remediation_executions", "verification_results", "ai_runs", "ai_checkpoints",
    "audit_events",
}


def validate() -> list[str]:
    errors: list[str] = []
    contract = json.loads((ROOT / "contracts/database-model.json").read_text())
    schema = (ROOT / "db/schema.sql").read_text()
    tables = set(re.findall(r"CREATE TABLE ([a-z_]+)", schema))
    if not REQUIRED_TABLES.issubset(tables):
        errors.append(f"missing tables: {sorted(REQUIRED_TABLES - tables)}")
    if contract.get("database") != "postgresql" or contract.get("minimum_version") != "16":
        errors.append("unsupported database contract")
    tenant_tables = REQUIRED_TABLES - {"tenants"}
    for table in tenant_tables:
        match = re.search(rf"CREATE TABLE {table} \((.*?)\n\);", schema, re.DOTALL)
        if not match or "tenant_id uuid NOT NULL" not in match.group(1):
            errors.append(f"tenant discriminator missing: {table}")
    if schema.count("FOREIGN KEY (tenant_id,") < 14:
        errors.append("composite tenant foreign keys are incomplete")
    for forbidden in ("password text", "access_token", "private_key"):
        if forbidden in schema.lower():
            errors.append(f"credential storage prohibited: {forbidden}")
    for invariant in ("tenant_id_is_immutable", "authorization_is_separate_from_ai_recommendation", "ai_checkpoint_never_grants_authority"):
        if invariant not in contract.get("invariants", []):
            errors.append(f"data invariant missing: {invariant}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("PostgreSQL data model validation passed")
