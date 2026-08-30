#!/usr/bin/env python3
"""Validate persona, permission, and segregation-of-duties contracts."""

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
    authority = load("personas-authority-model.json")
    synthetic = load("synthetic-personas.json")
    roles = authority.get("roles", {})
    personas = synthetic.get("personas", [])
    persona_ids = {persona.get("id") for persona in personas}

    required_roles = {"employee", "service_desk_engineer", "l2_l3_specialist", "remediation_approver", "endpoint_administrator", "network_administrator", "identity_exchange_administrator", "security_administrator", "tenant_administrator", "auditor"}
    if set(roles) != required_roles:
        errors.append("Human authority roles are incomplete or unexpected")
    if len(personas) < 25 or len(persona_ids) != len(personas):
        errors.append("At least 25 unique synthetic personas are required")
    if not synthetic.get("synthetic_only"):
        errors.append("Persona dataset must be explicitly synthetic-only")

    represented_roles = {persona.get("role") for persona in personas}
    if not required_roles.issubset(represented_roles):
        errors.append("Every authority role must have a synthetic persona")
    if any(persona.get("role") not in roles for persona in personas):
        errors.append("A synthetic persona references an undefined role")

    principles = set(authority.get("authorization_principles", []))
    for principle in {"default_deny", "least_privilege", "human_authority_is_never_inferred_by_llm", "requester_cannot_approve_own_high_risk_change"}:
        if principle not in principles:
            errors.append(f"Missing authorization principle: {principle}")

    if authority.get("break_glass", {}).get("llm_eligible") is not False:
        errors.append("LLM must never be eligible for break-glass authority")
    if not authority.get("segregation_of_duties"):
        errors.append("Segregation-of-duties rules are required")

    for assignment in synthetic.get("demo_assignments", []):
        for field in ("employee_id", "engineer_id", "specialist_id", "approver_id"):
            if assignment.get(field) not in persona_ids:
                errors.append(f"Demo assignment references unknown {field}")

    return errors


if __name__ == "__main__":
    validation_errors = validate()
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("DeskPilot personas and authority contracts are valid.")
