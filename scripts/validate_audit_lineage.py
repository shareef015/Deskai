from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/audit-evidence-policy.json").read_text())
    migration = (ROOT / "services/api/migrations/versions/0006_audit_and_evidence_lineage.py").read_text()
    service = (ROOT / "services/api/src/deskpilot_api/audit/service.py").read_text()
    audit = policy.get("audit", {})
    for key in ("update_allowed", "delete_allowed", "direct_runtime_insert_allowed"):
        if audit.get(key) is not False:
            errors.append(f"audit immutability control missing: {key}")
    for token in ("append_audit_event", "pg_advisory_xact_lock", "previous_hash", "digest(", "REVOKE INSERT, UPDATE, DELETE", "reject_immutable_mutation"):
        if token not in migration:
            errors.append(f"database audit control missing: {token}")
    for token in ("evidence_lineage_edges", "parent_evidence_id", "child_evidence_id", "legal_hold", "collector_version"):
        if token not in migration:
            errors.append(f"evidence lineage control missing: {token}")
    for token in ("PROHIBITED_KEYS", "request.safe_payload()", "append_audit_event"):
        if token not in service:
            errors.append(f"audit service control missing: {token}")
    if policy.get("retention", {}).get("legal_hold_overrides_expiry") is not True:
        errors.append("legal hold must override retention expiry")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("audit and evidence-lineage validation passed")
