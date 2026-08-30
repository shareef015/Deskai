from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/incident-event-policy.json").read_text())
    service = (ROOT / "services/api/src/deskpilot_api/incidents/events.py").read_text()
    migration = (ROOT / "services/api/migrations/versions/0009_incident_event_outbox.py").read_text()
    lifecycle = (ROOT / "services/api/src/deskpilot_api/incidents/lifecycle.py").read_text()
    if policy.get("outbox", {}).get("delivery") != "at_least_once": errors.append("outbox delivery semantics changed")
    if policy.get("transaction", {}).get("publish_inside_business_transaction") is not False: errors.append("events must not publish inside business transaction")
    for token in ("IncidentEvent(", "EventOutbox(", "self._session.add_all((event, outbox))", "65_536"):
        if token not in service: errors.append(f"event append control missing: {token}")
    for token in ("event_outbox_pending_idx", "protect_outbox_identity", "attempt_count BETWEEN 0 AND 12", "FORCE ROW LEVEL SECURITY"):
        if token not in migration: errors.append(f"outbox persistence control missing: {token}")
    if "IncidentEventService(uow.session" not in lifecycle: errors.append("lifecycle does not use transactional event service")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("incident event and outbox validation passed")
