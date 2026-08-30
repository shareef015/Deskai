from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/database-performance-policy.json").read_text())
    migration = (ROOT / "services/api/migrations/versions/0002_workload_indexes.py").read_text()
    queries = (ROOT / "db/query-plans/critical-queries.sql").read_text()
    targets = policy.get("targets", {})
    if targets.get("interactive_query_p95_ms", 999999) > targets.get("api_total_p95_ms", 0):
        errors.append("query latency budget exceeds API latency budget")
    if policy.get("pagination", {}).get("strategy") != "keyset":
        errors.append("large result pagination must use keyset cursors")
    required_indexes = (
        "incidents_open_work_idx", "consent_active_incident_idx",
        "approval_action_lookup_idx", "ai_checkpoint_resume_idx", "audit_correlation_idx",
    )
    for index in required_indexes:
        if index not in migration:
            errors.append(f"critical index missing: {index}")
    for query in queries.split(";"):
        if "SELECT " in query and "tenant_id" not in query:
            errors.append("critical query lacks tenant predicate")
    if " OFFSET " in queries.upper():
        errors.append("offset pagination found in critical queries")
    for control in ("pg_stat_statements_required", "index_creation_method_production"):
        if control not in policy.get("operations", {}):
            errors.append(f"database operations control missing: {control}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("PostgreSQL performance validation passed")
