#!/usr/bin/env python3
"""Validate the Windows printer catalogue and deterministic scenarios."""

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
    catalog = load("printer-support-catalog.json")
    scenarios = load("printer-synthetic-scenarios.json")
    sources = load("printer-knowledge-sources.json")
    incidents = catalog.get("incidents", [])
    incident_ids = {item.get("id") for item in incidents}
    allowed_risks = set(catalog.get("risk_levels", {}))

    if len(incidents) < 10:
        errors.append("Printer catalogue must define at least 10 incident classes")
    if len(incident_ids) != len(incidents):
        errors.append("Printer incident IDs must be unique")

    required = {"id", "name", "signals", "questions", "diagnostics", "hypotheses", "remediations", "verification"}
    for incident in incidents:
        missing = required - set(incident)
        if missing:
            errors.append(f"{incident.get('id', '<unknown>')} missing {sorted(missing)}")
        verification = set(incident.get("verification", []))
        if not {"physical_output_confirmed", "employee_confirms"}.issubset(verification):
            errors.append(f"{incident.get('id')} lacks physical output and employee verification")
        for remediation in incident.get("remediations", []):
            if remediation.get("risk") not in allowed_risks:
                errors.append(f"{incident.get('id')} has invalid risk")
            if not remediation.get("approval") or not remediation.get("rollback"):
                errors.append(f"{incident.get('id')} remediation lacks approval or rollback")

    if len(scenarios.get("scenarios", [])) < 10:
        errors.append("At least 10 deterministic printer scenarios are required")
    for scenario in scenarios.get("scenarios", []):
        if scenario.get("incident") not in incident_ids:
            errors.append(f"{scenario.get('id')} references an unknown incident")

    if len(sources.get("sources", [])) < 6:
        errors.append("Printer catalogue requires at least six authoritative sources")
    if any(source.get("authority") != "Microsoft" for source in sources.get("sources", [])):
        errors.append("Initial printer sources must be Microsoft authoritative sources")

    return errors


if __name__ == "__main__":
    validation_errors = validate()
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("DeskPilot printer support catalogue is valid.")
