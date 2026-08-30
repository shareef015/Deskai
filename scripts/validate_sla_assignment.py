from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/sla-assignment-policy.json").read_text())
    engine = (ROOT / "services/api/src/deskpilot_api/sla/engine.py").read_text()
    calendar = (ROOT / "services/api/src/deskpilot_api/sla/calendar.py").read_text()
    migration = (ROOT / "services/api/migrations/versions/0008_sla_assignment_and_escalation.py").read_text()
    if set(policy.get("targets", {})) != {"1", "2", "3", "4", "5"}: errors.append("SLA targets must cover priorities 1 through 5")
    if policy.get("pause", {}).get("acknowledgement_clock_pausable") is not False: errors.append("acknowledgement clock must not pause")
    for token in ("ZoneInfo", "working_weekdays", "holidays", "add_minutes"):
        if token not in calendar: errors.append(f"business calendar control missing: {token}")
    for token in ("utilization >= 100", "utilization >= 80", "unowned"):
        if token not in engine: errors.append(f"escalation calculation missing: {token}")
    for token in ("incident_active_assignment_unique_idx", "sla_one_open_pause_idx", "deduplication_key", "reject_immutable_mutation", "FORCE ROW LEVEL SECURITY"):
        if token not in migration: errors.append(f"SLA persistence control missing: {token}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("SLA assignment and escalation validation passed")
