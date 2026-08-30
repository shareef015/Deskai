from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/realtime-stream-policy.json").read_text())
    stream = (ROOT / "services/api/src/deskpilot_api/incidents/streaming.py").read_text()
    routes = (ROOT / "services/api/src/deskpilot_api/routes/incidents.py").read_text()
    repository = (ROOT / "services/api/src/deskpilot_api/database/repositories.py").read_text()
    if policy.get("transport") != "server_sent_events": errors.append("real-time transport changed")
    for token in ("request.is_disconnected()", 'yield ": heartbeat', "await asyncio.sleep(1)", "limit=100", "after_sequence"):
        if token not in stream: errors.append(f"SSE control missing: {token}")
    for token in ('Header(alias="Last-Event-ID")', "StreamingResponse", '"X-Accel-Buffering": "no"'):
        if token not in routes: errors.append(f"SSE route control missing: {token}")
    for token in ("IncidentEvent.sequence_number > after_sequence", "IncidentEvent.incident_id == incident_id"):
        if token not in repository: errors.append(f"SSE replay query missing: {token}")
    if policy.get("backpressure", {}).get("unbounded_queue_prohibited") is not True: errors.append("unbounded stream queue must be prohibited")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("real-time SSE validation passed")
