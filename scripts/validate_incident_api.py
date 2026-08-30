from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/incident-api-policy.json").read_text())
    routes = (ROOT / "services/api/src/deskpilot_api/routes/incidents.py").read_text()
    schemas = (ROOT / "services/api/src/deskpilot_api/incidents/schemas.py").read_text()
    repository = (ROOT / "services/api/src/deskpilot_api/database/repositories.py").read_text()
    service = (ROOT / "services/api/src/deskpilot_api/incidents/service.py").read_text()
    app = (ROOT / "services/api/src/deskpilot_api/app.py").read_text()
    if policy.get("tenant_source") != "authenticated_principal_only": errors.append("tenant source must be authenticated principal")
    if policy.get("delete_supported") is not False or "@router.delete" in routes: errors.append("incident deletion must remain unavailable")
    for token in ("Depends(require_principal)", 'Header(alias="If-Match")', '"private, no-store"'):
        if token not in routes: errors.append(f"incident route control missing: {token}")
    for token in ('extra="forbid"', "Field(ge=1, le=5)", "max_length=500"):
        if token not in schemas: errors.append(f"incident schema control missing: {token}")
    for token in ("Incident.version == expected_version", "cursor_opened_at", "cursor_id"):
        if token not in repository: errors.append(f"incident repository control missing: {token}")
    if "principal.tenant_id" not in service or "include_router(incident_router)" not in app: errors.append("incident API is not tenant-bound and registered")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("incident CRUD API validation passed")
