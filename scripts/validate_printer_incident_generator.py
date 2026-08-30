from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-printer-incident-generator-policy.json").read_text());path=ROOT/"data/synthetic/printer-incidents.json";data=json.loads(path.read_text());catalog=json.loads((ROOT/"contracts/printer-support-catalog.json").read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_printer_incidents.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("generated dataset is not deterministic")
 cases=data.get("cases",[]);required=set(policy["required_case_fields"])
 if len(cases)<policy["minimum_cases"] or data.get("case_count")!=len(cases):errors.append("case count is invalid")
 if any(required-set(c) for c in cases):errors.append("case fields are incomplete")
 if len({c.get("case_id") for c in cases})!=len(cases):errors.append("case ids are not unique")
 if {i["id"] for i in catalog["incidents"]}!={c.get("incident_id") for c in cases}:errors.append("catalog coverage is incomplete")
 if any(c.get("risk_level") not in policy["allowed_risk_levels"] or c.get("expected_final_status") not in policy["allowed_final_statuses"] for c in cases):errors.append("risk or status is invalid")
 if any(c.get("tenant_id")!=policy["tenant_id"] or not c.get("device_state",{}).get("synthetic") for c in cases):errors.append("non-synthetic or cross-tenant case")
 if any(c.get("verification",{}).get("test_print")!="synthetic_test_page" or not c.get("verification",{}).get("physical_output_confirmation_required") for c in cases):errors.append("physical test-print verification missing")
 if any(not c.get("topology",{}).get("queue") or len(c.get("timeline",[]))<5 for c in cases):errors.append("topology or timeline missing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic printer incident generator validation passed")
