from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/redis-state-policy.json").read_text())
    keys = (ROOT / "packages/python/deskpilot-core/src/deskpilot_core/redis_keys.py").read_text()
    sessions = (ROOT / "services/api/src/deskpilot_api/distributed_state/sessions.py").read_text()
    locks = (ROOT / "services/api/src/deskpilot_api/distributed_state/locks.py").read_text()
    if policy.get("keyspace", {}).get("tenant_namespace_hmac_required") is not True:
        errors.append("tenant key namespaces must use keyed HMAC")
    for token in ("hmac.new", "tenant_namespace", "Redis key exceeds maximum length"):
        if token not in keys:
            errors.append(f"Redis key safety missing: {token}")
    for token in ("AESGCM", "os.urandom(12)", "session_id.encode()", "getex"):
        if token not in sessions:
            errors.append(f"encrypted session control missing: {token}")
    for token in ("nx=True", "px=self._ttl_ms", "secrets.token_urlsafe", "redis.call('GET'", "redis.call('DEL'"):
        if token not in locks:
            errors.append(f"distributed lock control missing: {token}")
    modes = policy.get("failure_modes", {})
    if modes.get("session_unavailable") != "fail_closed_503":
        errors.append("session outage must fail closed")
    if modes.get("read_cache_unavailable") != "bypass_to_authoritative_store":
        errors.append("read cache outage must bypass safely")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Redis distributed-state validation passed")
