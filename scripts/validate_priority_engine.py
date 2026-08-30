from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/priority-severity-policy.json").read_text())
    engine = (ROOT / "services/api/src/deskpilot_api/incidents/priority.py").read_text()
    migration = (ROOT / "services/api/migrations/versions/0007_priority_and_severity.py").read_text()
    service = (ROOT / "services/api/src/deskpilot_api/incidents/service.py").read_text()
    if policy.get("authority") != "deterministic_policy_engine": errors.append("priority authority must be deterministic")
    if policy.get("client_supplied_final_priority_allowed") is not False or policy.get("llm_supplied_final_priority_allowed") is not False: errors.append("client or LLM final priority must be prohibited")
    for token in ("security_or_safety_risk", "complete_site_outage", "impact_urgency_score_", "POLICY_VERSION"):
        if token not in engine: errors.append(f"priority engine control missing: {token}")
    for token in ("incident_priority_overrides", "original_priority", "authorized_by", "expires_at", "reject_immutable_mutation"):
        if token not in migration: errors.append(f"priority override control missing: {token}")
    if "classify_priority(" not in service or "command.priority" in service: errors.append("incident creation does not use deterministic classification")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("priority and severity validation passed")
