#!/usr/bin/env python3
"""Validate the Outlook support catalogue and deterministic demo cases."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


def load(name: str) -> dict:
    with (CONTRACTS / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate() -> list[str]:
    errors: list[str] = []
    catalog = load("outlook-support-catalog.json")
    scenarios = load("outlook-synthetic-scenarios.json")
    sources = load("knowledge-sources.json")
    incidents = catalog.get("incidents", [])
    incident_ids = {item.get("id") for item in incidents}

    if len(incidents) < 10:
        errors.append("Outlook catalogue must define at least 10 incident classes")
    if len(incident_ids) != len(incidents):
        errors.append("Outlook incident IDs must be unique")

    allowed_clients = set(catalog.get("clients", {}))
    allowed_risks = set(catalog.get("risk_levels", {}))
    for incident in incidents:
        required = {"id", "name", "clients", "signals", "questions", "diagnostics", "hypotheses", "remediations", "verification"}
        missing = required - set(incident)
        if missing:
            errors.append(f"{incident.get('id', '<unknown>')} missing {sorted(missing)}")
        if not set(incident.get("clients", [])).issubset(allowed_clients):
            errors.append(f"{incident.get('id')} references an unsupported Outlook client")
        if "employee_confirms" not in incident.get("verification", []):
            errors.append(f"{incident.get('id')} lacks employee confirmation")
        for remediation in incident.get("remediations", []):
            if remediation.get("risk") not in allowed_risks:
                errors.append(f"{incident.get('id')} has invalid remediation risk")
            if not remediation.get("approval") or not remediation.get("rollback"):
                errors.append(f"{incident.get('id')} remediation lacks approval or rollback")

    if len(scenarios.get("scenarios", [])) < 10:
        errors.append("At least 10 deterministic Outlook demo scenarios are required")
    for scenario in scenarios.get("scenarios", []):
        if scenario.get("incident") not in incident_ids:
            errors.append(f"{scenario.get('id')} references an unknown incident")

    if len(sources.get("sources", [])) < 5:
        errors.append("The catalogue requires at least five authoritative sources")
    if any(source.get("authority") != "Microsoft" for source in sources.get("sources", [])):
        errors.append("Initial Outlook sources must be Microsoft authoritative sources")

    return errors


if __name__ == "__main__":
    validation_errors = validate()
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("DeskPilot Outlook support catalogue is valid.")
