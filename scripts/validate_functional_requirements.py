#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "contracts" / "functional-requirements.json"
def load() -> dict: return json.loads(PATH.read_text(encoding="utf-8"))
def validate() -> list[str]:
    data = load(); errors: list[str] = []; reqs = data["requirements"]; uses = data["use_cases"]
    ids = [r["id"] for r in reqs]
    if len(reqs) < 18 or len(ids) != len(set(ids)): errors.append("At least 18 unique functional requirements are required")
    if len(uses) < 8: errors.append("At least eight use cases are required")
    for use in uses:
        if not use.get("preconditions") or not use.get("success") or not use.get("alternative"): errors.append(f"{use.get('id')} lacks complete paths")
    required_caps = {"consent", "diagnostics", "rag", "approval", "execution", "verification", "confirmation", "audit"}
    if not required_caps.issubset({r["capability"] for r in reqs}): errors.append("Critical capabilities are missing")
    return errors
if __name__ == "__main__":
    errors = validate()
    if errors: print("\n".join(f"ERROR: {e}" for e in errors)); raise SystemExit(1)
    print("DeskPilot functional requirements are valid.")
