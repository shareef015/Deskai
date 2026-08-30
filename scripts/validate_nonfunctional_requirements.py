#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
PATH = Path(__file__).resolve().parents[1] / "contracts" / "nonfunctional-requirements.json"
def load() -> dict: return json.loads(PATH.read_text(encoding="utf-8"))
def validate() -> list[str]:
    data = load(); errors: list[str] = []
    if len(data["slos"]) < 8 or len(data["quality_kpis"]) < 8: errors.append("SLO or KPI set is incomplete")
    zero_ids = {"SLO-006", "SLO-007", "SLO-008"}
    values = {x["id"]: x["target"] for x in data["slos"]}
    if any(values.get(i) != 0 for i in zero_ids): errors.append("Security invariants must target zero violations")
    budget = data["budget"]
    if budget["ten_device_monthly_platform_soft_limit"] >= budget["ten_device_monthly_platform_hard_limit"]: errors.append("Soft limit must be below hard limit")
    if "without_bypassing_safety" not in budget["hard_limit_behavior"]: errors.append("Budget exhaustion must preserve safety")
    if data["security"]["critical_vulnerability_release_threshold"] != 0: errors.append("Critical vulnerability threshold must be zero")
    return errors
if __name__ == "__main__":
    errors = validate()
    if errors: print("\n".join(f"ERROR: {e}" for e in errors)); raise SystemExit(1)
    print("DeskPilot non-functional requirements are valid.")
