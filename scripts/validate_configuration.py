from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/configuration-policy.json").read_text())
    profiles = ROOT / "config/environments"
    for environment in policy["environments"]:
        path = profiles / f"{environment}.json"
        if not path.is_file():
            errors.append(f"missing profile: {environment}")
            continue
        profile = json.loads(path.read_text())
        if profile.get("environment") != environment:
            errors.append(f"profile identity mismatch: {environment}")
        if set(profile.get("managed_endpoint_operating_systems", [])) != {"windows_10", "windows_11"}:
            errors.append(f"invalid endpoint OS boundary: {environment}")
    production = json.loads((profiles / "production.json").read_text())
    for key, expected in policy["production_invariants"].items():
        if production.get(key) != expected:
            errors.append(f"production invariant failed: {key}")
    text = "\n".join(path.read_text() for path in ROOT.rglob("*.json"))
    if "BEGIN PRIVATE KEY" in text:
        errors.append("private key material committed")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("configuration validation passed")
