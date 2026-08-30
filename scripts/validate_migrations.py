from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/migration-policy.json").read_text())
    schema = (ROOT / "db/schema.sql").read_bytes()
    migration = (ROOT / "services/api/migrations/versions/0001_initial_schema.py").read_text()
    environment = (ROOT / "services/api/migrations/env.py").read_text()
    digest = hashlib.sha256(schema).hexdigest()
    if digest != policy.get("baseline_schema_sha256") or digest not in migration:
        errors.append("baseline schema digest mismatch")
    for token in ("pg_advisory_xact_lock", "def upgrade()", "def downgrade()", "DROP_ORDER"):
        if token not in migration:
            errors.append(f"baseline migration control missing: {token}")
    for token in ("DESKPILOT_DATABASE_URL", "transaction_per_migration=True", "compare_type=True"):
        if token not in environment:
            errors.append(f"Alembic environment control missing: {token}")
    ini = (ROOT / "services/api/alembic.ini").read_text()
    if "password" in ini.lower() or "${" in ini:
        errors.append("Alembic configuration may contain a credential")
    required = set(policy.get("deployment_controls", []))
    if "upgrade_then_downgrade_then_upgrade_test_required" not in required:
        errors.append("rollback round-trip test policy missing")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Alembic migration validation passed")
