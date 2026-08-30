from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/durable-job-policy.json").read_text())
    store = (ROOT / "services/api/src/deskpilot_api/jobs/store.py").read_text()
    migration = (ROOT / "services/api/migrations/versions/0010_durable_jobs.py").read_text()
    runner = (ROOT / "services/worker/src/deskpilot_worker/runner.py").read_text()
    if policy.get("delivery") != "at_least_once": errors.append("job delivery semantics changed")
    for token in ("FOR UPDATE SKIP LOCKED", "secrets.token_urlsafe", "lease_expires_at>:now", "ON CONFLICT"):
        if token not in store: errors.append(f"durable job control missing: {token}")
    for token in ("durable_job_attempts", "job_max_attempts", "protect_job_attempt_identity", "FORCE ROW LEVEL SECURITY"):
        if token not in migration: errors.append(f"job persistence control missing: {token}")
    if "self._handlers[(job_type, schema_version)]" not in runner: errors.append("typed job registry missing")
    if policy.get("safety", {}).get("arbitrary_code_job_prohibited") is not True: errors.append("arbitrary jobs must be prohibited")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("durable background job validation passed")
