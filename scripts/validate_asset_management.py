from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/asset-management-policy.json").read_text())
    migration = (ROOT / "services/api/migrations/versions/0005_asset_inventory.py").read_text()
    lifecycle = (ROOT / "services/api/src/deskpilot_api/inventory/lifecycle.py").read_text()
    if set(policy.get("endpoint_operating_systems", [])) != {"windows_10", "windows_11"}:
        errors.append("endpoint operating-system boundary changed")
    ownership = policy.get("ownership", {})
    for key in ("one_active_primary_assignment_per_device", "assignment_requires_same_tenant", "employee_may_not_self_assign"):
        if ownership.get(key) is not True:
            errors.append(f"ownership control missing: {key}")
    for token in ("device_assignments", "device_primary_assignment_unique_idx", "serial_fingerprint", "FORCE ROW LEVEL SECURITY"):
        if token not in migration:
            errors.append(f"inventory persistence control missing: {token}")
    for token in ("expected_version != self.version", '"retired": frozenset()', "assignment tenant mismatch"):
        if token not in lifecycle:
            errors.append(f"inventory domain control missing: {token}")
    if policy.get("privacy", {}).get("raw_serial_number_storage_allowed") is not False:
        errors.append("raw serial storage must be prohibited")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("asset management validation passed")
