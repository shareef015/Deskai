from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/authorization-policy.json").read_text())
    engine = (ROOT / "services/api/src/deskpilot_api/auth/rbac.py").read_text()
    migration = (ROOT / "services/api/migrations/versions/0004_role_assignments.py").read_text()
    if policy.get("decision_model") != "deny_by_default" or policy.get("deny_overrides_allow") is not True:
        errors.append("authorization must deny by default with deny precedence")
    if policy.get("token_roles_are_authorization_hints_only") is not True:
        errors.append("token roles must not be authoritative")
    for token in ("explicit_deny", "no_matching_allow", "segregation_of_duties_proposer", "assignment.tenant_id == request.tenant_id"):
        if token not in engine:
            errors.append(f"authorization control missing: {token}")
    for token in ("role_assignments", "valid_until", "revoked_at", "FORCE ROW LEVEL SECURITY", "WITH CHECK"):
        if token not in migration:
            errors.append(f"role assignment persistence control missing: {token}")
    if len(policy.get("segregation_of_duties", [])) < 5:
        errors.append("segregation-of-duties policy incomplete")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("enterprise authorization validation passed")
