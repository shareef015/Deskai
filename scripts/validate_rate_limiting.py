from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/rate-limit-policy.json").read_text())
    code = (ROOT / "services/api/src/deskpilot_api/rate_limiting.py").read_text()
    routes = (ROOT / "services/api/src/deskpilot_api/routes/incidents.py").read_text()
    if set(policy.get("dimensions", {})) != {"tenant", "user", "network"}: errors.append("rate-limit dimensions changed")
    for token in ("redis.call('TIME')", "if retry_after > 0 then return", "HSET", "hmac.new", "RateLimit-Remaining"):
        if token not in code: errors.append(f"rate-limit control missing: {token}")
    if "Depends(enforce_rate_limit)" not in routes: errors.append("incident routes do not enforce distributed limits")
    if policy.get("failure", {}).get("silent_local_fallback_prohibited") is not True: errors.append("local fallback must be prohibited")
    if policy.get("atomicity", {}).get("partial_bucket_consumption_prohibited") is not True: errors.append("partial consumption must be prohibited")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("distributed rate-limit validation passed")
