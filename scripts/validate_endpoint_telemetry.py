from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-endpoint-telemetry-policy.json").read_text());path=ROOT/"data/synthetic/endpoint-telemetry.json";data=json.loads(path.read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_endpoint_telemetry.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("telemetry dataset is not deterministic")
 packs=data.get("packs",[]);results=[r for p in packs for r in p.get("results",[])]
 if len(packs)<policy["minimum_packs"] or data.get("pack_count")!=len(packs) or data.get("result_count")!=len(results):errors.append("pack or result count is invalid")
 if any(len(p.get("results",[]))<policy["minimum_results_per_pack"] or len(p["results"])>policy["maximum_results_per_pack"] for p in packs):errors.append("results per pack are out of bounds")
 required=set(policy["required_result_fields"])
 if any(required-set(r) for r in results):errors.append("typed result fields are incomplete")
 if not set(policy["statuses"]).issubset({r.get("status") for r in results}):errors.append("success/failure/timeout/partial coverage is incomplete")
 if any(r.get("duration_ms",0)>policy["maximum_duration_ms"] or r.get("tenant_id") for r in results):errors.append("duration or result tenancy is invalid")
 if any(not r.get("redaction",{}).get("applied") or r.get("output",{}).get("content_included") is not False for r in results):errors.append("redaction or content safety is invalid")
 if any("powershell" in r.get("capability_id","").lower() or "shell" in r.get("capability_id","").lower() for r in results):errors.append("unrestricted command capability found")
 if any(r.get("correlation_id")!=p.get("correlation_id") or r.get("incident_case_id")!=p.get("incident_case_id") or r.get("endpoint_id")!=p.get("endpoint_id") for p in packs for r in p["results"]):errors.append("evidence lineage is broken")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic endpoint telemetry and command-result validation passed")
