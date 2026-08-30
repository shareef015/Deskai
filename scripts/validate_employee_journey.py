#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "contracts" / "employee-support-journey.json"

def load() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))

def validate() -> list[str]:
    data = load(); errors: list[str] = []
    states = set(data["states"])
    if not set(data["required_sequence"]).issubset(states): errors.append("Required sequence references unknown state")
    if data["required_sequence"].index("awaiting_diagnostic_consent") > data["required_sequence"].index("diagnosing"): errors.append("Consent must precede diagnostics")
    if data["required_sequence"].index("awaiting_remediation_authorization") > data["required_sequence"].index("remediating"): errors.append("Authorization must precede remediation")
    if data["required_sequence"][-3:] != ["technical_verification", "awaiting_employee_confirmation", "resolved"]: errors.append("Closure sequence is invalid")
    if data["bounded_behavior"]["on_limit"] != "escalate_with_evidence": errors.append("Bounded exhaustion must escalate")
    return errors

if __name__ == "__main__":
    errors = validate()
    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors)); raise SystemExit(1)
    print("DeskPilot employee support journey is valid.")
