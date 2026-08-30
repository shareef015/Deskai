from __future__ import annotations
import importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path:str)->dict: return json.loads((ROOT/path).read_text(encoding="utf-8"))
def validate()->list[str]:
    policy=load("contracts/synthetic-device-inventory-policy.json"); fixture=load(policy["fixture"]); endpoints=load("data/synthetic/endpoints.json")["endpoints"]; errors=[]
    inventories=fixture.get("inventories",[]); endpoint_ids={e["id"] for e in endpoints}; req=policy["requirements"]
    if not fixture.get("synthetic_only") or fixture.get("seed")!=policy["seed"]: errors.append("inventory seed mismatch")
    if {i["endpoint_id"] for i in inventories}!=endpoint_ids or len(inventories)!=10: errors.append("inventory endpoint coverage mismatch")
    if any(i["tenant_id"]!=policy["tenant_id"] for i in inventories): errors.append("inventory tenant mismatch")
    if any(not all(i.get(kind) for kind in ("applications","services","drivers","peripherals","dependencies")) for i in inventories): errors.append("inventory class missing")
    if any(not all(a.get("version") and a.get("health") for a in i["applications"]) for i in inventories): errors.append("application metadata incomplete")
    if any(not all("expected" in s and "observed" in s and "startup" in s for s in i["services"]) for i in inventories): errors.append("service health contract incomplete")
    if any(not all(d.get("provider") and d.get("version") and d.get("signed") is True for d in i["drivers"]) for i in inventories): errors.append("driver trust metadata invalid")
    if any(not all(p.get("synthetic") is True for p in i["peripherals"]) for i in inventories): errors.append("non-synthetic peripheral")
    if not req["secrets_and_license_keys_forbidden"] or not req["expected_and_observed_state_separate"]: errors.append("inventory safety invariant missing")
    spec=importlib.util.spec_from_file_location("inventory_generator",ROOT/"data/synthetic/generate_device_inventory.py"); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if (ROOT/policy["fixture"]).read_bytes()!=module.canonical_bytes(): errors.append("inventory replay mismatch")
    return errors
if __name__=="__main__":
    failures=validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic device inventory validation passed")
