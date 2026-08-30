from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/idempotency-policy.json").read_text())
    code = (ROOT / "services/api/src/deskpilot_api/idempotency.py").read_text()
    migration = (ROOT / "services/api/migrations/versions/0011_idempotency_records.py").read_text()
    routes = (ROOT / "services/api/src/deskpilot_api/routes/incidents.py").read_text()
    if policy.get("scope") != ["tenant_id", "operation", "idempotency_key"]: errors.append("idempotency scope changed")
    for token in ("sort_keys=True", "fingerprint_conflict", "in_progress", "AESGCM", "owner_token_hash", "lease_expires_at>:now"):
        if token not in code: errors.append(f"idempotency control missing: {token}")
    for token in ("idempotency_records", "protect_idempotency_identity", "FORCE ROW LEVEL SECURITY", "response_envelope"):
        if token not in migration: errors.append(f"idempotency persistence missing: {token}")
    if routes.count('Header(alias="Idempotency-Key")') < 3: errors.append("mutating incident routes must require idempotency keys")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("idempotency validation passed")
