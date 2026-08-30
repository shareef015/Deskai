from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-windows-network-incident-generator-policy.json").read_text());path=ROOT/"data/synthetic/windows-network-incidents.json";data=json.loads(path.read_text());catalog=json.loads((ROOT/"contracts/windows-network-support-catalog.json").read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_windows_network_incidents.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("generated dataset is not deterministic")
 cases=data.get("cases",[]);required=set(policy["required_case_fields"])
 if len(cases)<policy["minimum_cases"] or data.get("case_count")!=len(cases):errors.append("case count is invalid")
 if any(required-set(c) for c in cases):errors.append("case fields are incomplete")
 if len({c.get("case_id") for c in cases})!=len(cases):errors.append("case ids are not unique")
 if {i["id"] for i in catalog["incidents"]}!={c.get("incident_id") for c in cases}:errors.append("catalog coverage is incomplete")
 if any(c.get("risk_level") not in policy["allowed_risk_levels"] or c.get("expected_final_status") not in policy["allowed_final_statuses"] for c in cases):errors.append("risk or status is invalid")
 if any(c.get("tenant_id")!=policy["tenant_id"] or not c.get("device_state",{}).get("synthetic") for c in cases):errors.append("non-synthetic or cross-tenant case")
 for case in cases:
  verification=case.get("verification",{})
  if verification.get("original_business_function") not in policy["business_functions"] or not verification.get("business_function_success_required") or verification.get("ping_or_dns_alone_sufficient") is not False:errors.append("business-function verification is invalid");break
 if any(len(c.get("verification",{}).get("layer_checks",[]))<7 or len(c.get("timeline",[]))<5 for c in cases):errors.append("layer isolation or timeline is incomplete")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic Windows and network incident generator validation passed")
