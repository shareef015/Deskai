from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/structured-logging-policy.json").read_text())
    required = {"timestamp", "level", "event", "service", "environment", "correlation_id", "fields"}
    if set(policy.get("required_fields", [])) != required:
        errors.append("structured log required fields changed")
    privacy = policy.get("privacy", {})
    if privacy.get("secret_values") != "redacted" or privacy.get("hidden_reasoning") != "prohibited":
        errors.append("logging privacy controls are unsafe")
    targets = set(policy.get("correlation", {}).get("propagated_to", []))
    if targets != {"api", "worker", "langgraph", "rag", "mcp_gateway", "endpoint_agent", "audit"}:
        errors.append("correlation propagation is incomplete")
    source = ROOT / "packages/python/deskpilot-core/src/deskpilot_core/structured_logging.py"
    if not source.is_file():
        errors.append("structured logging implementation missing")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("structured logging validation passed")
