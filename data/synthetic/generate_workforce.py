from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "contracts/synthetic-personas.json"
DESTINATION = Path(__file__).with_name("workforce.json")

SUPPORT = {
    "usr-016": ("service-desk", ["outlook", "printer", "scanner", "windows_network"], "early_support"),
    "usr-017": ("service-desk", ["outlook", "printer", "scanner", "windows_network"], "late_support"),
    "usr-018": ("endpoint-engineering", ["outlook", "printer", "scanner", "endpoint"], "on_call"),
    "usr-020": ("endpoint-engineering", ["endpoint", "printer", "scanner"], "business_day"),
    "usr-021": ("network-engineering", ["network", "windows_network"], "on_call"),
    "usr-022": ("identity-messaging", ["identity", "outlook"], "on_call"),
    "usr-023": ("cybersecurity", ["security"], "on_call"),
}

def build() -> dict:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    people = []
    for persona in source["personas"]:
        number = int(persona["id"].split("-")[1])
        root = persona["id"] == "usr-013"
        support = SUPPORT.get(persona["id"])
        people.append({
            "id": persona["id"], "display_name": persona["name"], "tenant_id": source["tenant"]["id"],
            "department": persona["department"], "role": persona["role"],
            "manager_id": None if root else ("usr-013" if number <= 15 else "usr-024"),
            "location_id": "loc-warehouse" if persona["department"] == "Warehouse" else ("loc-branch" if persona["department"] == "Customer Care" else "loc-hq"),
            "employment_status": "active", "support_group_id": support[0] if support else None,
            "skills": support[1] if support else [], "shift": support[2] if support else "business_day",
            "device_ids": persona["device_ids"]
        })
    return {"schema_version":"1.0.0","synthetic_only":True,"seed":42001,"tenant_id":source["tenant"]["id"],"people":people}

def canonical_bytes() -> bytes:
    return (json.dumps(build(), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()

if __name__ == "__main__":
    DESTINATION.write_bytes(canonical_bytes())
    print(DESTINATION)
