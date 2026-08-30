from __future__ import annotations
import importlib.util, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path:str)->dict: return json.loads((ROOT/path).read_text(encoding="utf-8"))
def validate()->list[str]:
    policy=load("contracts/synthetic-endpoint-policy.json"); fixture=load(policy["fixture"]); workforce=load("data/synthetic/workforce.json"); org=load("data/synthetic/organization.json"); errors=[]
    endpoints=fixture.get("endpoints",[]); users={p["id"] for p in workforce["people"]}; locations={l["id"] for l in org["locations"]}
    if not fixture.get("synthetic_only") or fixture.get("seed")!=policy["seed"]: errors.append("endpoint seed mismatch")
    if len(endpoints)!=policy["endpoint_count"] or len({d["id"] for d in endpoints})!=10 or len({d["hostname"] for d in endpoints})!=10: errors.append("ten unique endpoints required")
    distribution={name:sum(d["operating_system"]==name for d in endpoints) for name in policy["os_distribution"]}
    if distribution!=policy["os_distribution"]: errors.append("operating system distribution mismatch")
    if any(d["tenant_id"]!=policy["tenant_id"] or d["primary_user_id"] not in users or d["location_id"] not in locations for d in endpoints): errors.append("endpoint relationship mismatch")
    if any(not re.fullmatch(r"[0-9a-f]{64}",d["serial_fingerprint"]) for d in endpoints): errors.append("serial fingerprint invalid")
    if any(d["architecture"]!="x64" or not all(k in d for k in ("hardware","installed_software","security_posture","baseline_health")) for d in endpoints): errors.append("endpoint profile incomplete")
    if any(d["lifecycle_status"]!="restricted" for d in endpoints if d["operating_system"]=="windows_10" and d["support_entitlement"]=="none"): errors.append("unsupported Windows 10 endpoint not restricted")
    spec=importlib.util.spec_from_file_location("endpoint_generator",ROOT/"data/synthetic/generate_endpoints.py"); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if (ROOT/policy["fixture"]).read_bytes()!=module.canonical_bytes(): errors.append("endpoint replay mismatch")
    return errors
if __name__=="__main__":
    failures=validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic endpoint validation passed")
