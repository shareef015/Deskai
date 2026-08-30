from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-outlook-incident-generator-policy.json").read_text());path=ROOT/"data/synthetic/outlook-incidents.json";data=json.loads(path.read_text());catalog=json.loads((ROOT/"contracts/outlook-support-catalog.json").read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_outlook_incidents.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("generated dataset is not deterministic")
 cases=data.get("cases",[])
 if len(cases)<policy["minimum_cases"] or data.get("case_count")!=len(cases):errors.append("case count is invalid")
 required=set(policy["required_case_fields"])
 if any(required-set(case) for case in cases):errors.append("case fields are incomplete")
 if len({case.get("case_id") for case in cases})!=len(cases):errors.append("case ids are not unique")
 if {i["id"] for i in catalog["incidents"]}!={c.get("incident_id") for c in cases}:errors.append("catalog coverage is incomplete")
 if any(c.get("risk_level") not in policy["allowed_risk_levels"] or c.get("expected_final_status") not in policy["allowed_final_statuses"] for c in cases):errors.append("risk or final status is invalid")
 if any(c.get("tenant_id")!=policy["tenant_id"] or not c.get("device_state",{}).get("synthetic") for c in cases):errors.append("non-synthetic or cross-tenant case")
 if any(len(c.get("timeline",[]))<4 or not c.get("verification") for c in cases):errors.append("timeline or verification missing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic Outlook incident generator validation passed")
