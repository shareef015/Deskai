from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/incident-lifecycle-policy.json").read_text())
    machine = (ROOT / "services/api/src/deskpilot_api/incidents/state_machine.py").read_text()
    service = (ROOT / "services/api/src/deskpilot_api/incidents/lifecycle.py").read_text()
    repository = (ROOT / "services/api/src/deskpilot_api/database/repositories.py").read_text()
    if set(policy.get("terminal_states", [])) != {"resolved", "cancelled"}: errors.append("terminal states changed")
    if policy.get("transitions", {}).get("resolved") != []: errors.append("resolved must be terminal")
    for token in ("transition_guard_failed", "technical_verification_passed", "employee_confirmation_received", "audit_events_complete"):
        if token not in machine: errors.append(f"state-machine control missing: {token}")
    for token in ("Incident.version == expected_version", "Incident.status == current_status", ".returning(Incident.version)"):
        if token not in repository: errors.append(f"atomic transition control missing: {token}")
    for token in ("IncidentEventService(uow.session", "AuditWriter(uow.session).append", "await uow.commit()"):
        if token not in service: errors.append(f"durable transition control missing: {token}")
    if policy.get("authority", {}).get("guard_evidence_from_client_body_allowed") is not False: errors.append("client guard assertions must be prohibited")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("incident lifecycle validation passed")
