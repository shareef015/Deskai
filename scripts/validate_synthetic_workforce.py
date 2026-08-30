from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: str) -> dict: return json.loads((ROOT / path).read_text(encoding="utf-8"))

def validate() -> list[str]:
    policy = load("contracts/synthetic-workforce-policy.json"); workforce = load(policy["fixture"]); org = load("data/synthetic/organization.json")
    errors: list[str] = []; req = policy["requirements"]; people = workforce.get("people", []); ids = {p["id"] for p in people}
    if not workforce.get("synthetic_only") or workforce.get("seed") != policy["seed"]: errors.append("synthetic seed mismatch")
    if workforce.get("tenant_id") != policy["tenant_id"] or any(p["tenant_id"] != policy["tenant_id"] for p in people): errors.append("workforce tenant mismatch")
    if len(people) < req["minimum_people"] or len(ids) != len(people): errors.append("workforce identities incomplete or duplicated")
    roots = [p for p in people if p["manager_id"] is None]
    if len(roots) != 1 or any(p["manager_id"] not in ids for p in people if p["manager_id"]): errors.append("reporting hierarchy invalid")
    groups = {g["id"] for g in org["support_groups"]}; locations = {l["id"] for l in org["locations"]}
    if any(p["location_id"] not in locations for p in people): errors.append("unknown workforce location")
    if any(p["support_group_id"] not in groups for p in people if p["support_group_id"]): errors.append("unknown support group")
    skills = {skill for p in people for skill in p["skills"]}
    if not set(req["support_coverage_domains"]).issubset(skills): errors.append("support skill coverage incomplete")
    if any(p["shift"] not in req["shifts"] for p in people): errors.append("unknown shift")
    spec = importlib.util.spec_from_file_location("workforce_generator", ROOT / "data/synthetic/generate_workforce.py")
    assert spec and spec.loader; module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if (ROOT / policy["fixture"]).read_bytes() != module.canonical_bytes(): errors.append("workforce fixture is not deterministic")
    return errors

if __name__ == "__main__":
    failures=validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic workforce validation passed")
