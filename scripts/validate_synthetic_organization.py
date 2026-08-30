from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def validate() -> list[str]:
    policy = load("contracts/synthetic-organization-policy.json")
    org = load(policy["fixture"])
    personas = load("contracts/synthetic-personas.json")
    errors: list[str] = []
    requirements = policy["requirements"]
    if not org.get("synthetic_only") or org.get("seed") != policy["seed"]: errors.append("synthetic seed contract mismatch")
    if org.get("tenant", {}).get("id") != policy["tenant_id"]: errors.append("tenant mismatch")
    locations, departments, groups = org.get("locations", []), org.get("departments", []), org.get("support_groups", [])
    location_ids = {item["id"] for item in locations}; department_ids = {item["id"] for item in departments}
    if len(locations) < requirements["minimum_locations"]: errors.append("insufficient locations")
    if not set(requirements["required_location_types"]).issubset({item["type"] for item in locations}): errors.append("required location types missing")
    if len(departments) < requirements["minimum_departments"]: errors.append("insufficient departments")
    if any(item["parent_id"] and item["parent_id"] not in department_ids for item in departments): errors.append("invalid department parent")
    if any(not set(item["location_ids"]).issubset(location_ids) for item in departments): errors.append("invalid department location")
    if set(requirements["support_groups"]) != {item["id"] for item in groups}: errors.append("support group mismatch")
    if any(item["department_id"] not in department_ids for item in groups): errors.append("invalid support group department")
    names = {item["name"] for item in departments}
    if any(persona["department"] not in names for persona in personas["personas"]): errors.append("persona department is absent from organization")
    return errors

if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic organization validation passed")
