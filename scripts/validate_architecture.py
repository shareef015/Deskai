#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
PATH = Path(__file__).resolve().parents[1] / "contracts" / "system-architecture.json"
def load() -> dict: return json.loads(PATH.read_text(encoding="utf-8"))
def validate() -> list[str]:
    data = load(); errors: list[str] = []
    required = {"web", "api", "ai_service", "rag_service", "mcp_gateway", "worker", "postgresql", "redis", "endpoint_agent", "telemetry"}
    if set(data["components"]) != required: errors.append("Architecture component set is incomplete")
    if "ai_service_direct_to_endpoint_agent" not in data["prohibited_connections"]: errors.append("Direct AI endpoint access must be prohibited")
    if data["data_authority"]["durable_truth"] != "postgresql": errors.append("PostgreSQL must be durable truth")
    if data["components"]["ai_service"]["authority"] != "proposal_only": errors.append("AI authority must be proposal-only")
    pilot = data["deployment_profiles"]["private_single_server_pilot"]
    if pilot["availability_class"] != "single_node_non_ha" or not pilot["required_off_host_backup"]: errors.append("Pilot availability statement is unsafe")
    if not any(x["from"] == "mcp_gateway" and x["to"] == "endpoint_agent" and x["protocol"] == "mutual_tls" for x in data["required_flows"]): errors.append("Endpoint mTLS flow is missing")
    return errors
if __name__ == "__main__":
    errors = validate()
    if errors: print("\n".join(f"ERROR: {e}" for e in errors)); raise SystemExit(1)
    print("DeskPilot system architecture is valid.")
