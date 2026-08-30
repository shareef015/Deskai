from __future__ import annotations
import importlib.util, ipaddress, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path:str)->dict: return json.loads((ROOT/path).read_text(encoding="utf-8"))
def validate()->list[str]:
    policy=load("contracts/synthetic-network-policy.json"); fixture=load(policy["fixture"]); endpoints=load("data/synthetic/endpoints.json")["endpoints"]; errors=[]
    states=fixture.get("endpoint_states",[]); topology=fixture.get("topology",{}); req=policy["requirements"]
    if not fixture.get("synthetic_only") or fixture.get("seed")!=policy["seed"]: errors.append("network seed mismatch")
    if {s["endpoint_id"] for s in states}!={e["id"] for e in endpoints} or len(states)!=10: errors.append("endpoint network coverage mismatch")
    addresses=[s["adapter"]["address"] for s in states]+[x["address"] for x in topology.get("dns_servers",[])]+[topology.get("proxy",{}).get("address","")]
    if any(not ipaddress.ip_address(value).is_private for value in addresses): errors.append("non-private address in topology")
    if any(s["tenant_id"]!=policy["tenant_id"] or s["active_faults"] for s in states): errors.append("baseline tenant or fault state invalid")
    if any(s["proxy"]["credentials_present"] or s["vpn"]["secret_material_present"] or (s["wifi"] and s["wifi"]["key_material_present"]) for s in states): errors.append("network secret material present")
    if set(policy["fault_types"])!={f["type"] for f in fixture.get("fault_catalog",[])}: errors.append("fault catalog mismatch")
    if any(not ("restore_value" in f or f.get("restore_from_baseline")) for f in fixture.get("fault_catalog",[])): errors.append("fault lacks rollback")
    if not req["expected_and_observed_state_separate"] or not policy["reset"]["clear_all_injected_faults"]: errors.append("state/reset invariant missing")
    spec=importlib.util.spec_from_file_location("network_generator",ROOT/"data/synthetic/generate_network_environment.py"); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if (ROOT/policy["fixture"]).read_bytes()!=module.canonical_bytes(): errors.append("network replay mismatch")
    return errors
if __name__=="__main__":
    failures=validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic network validation passed")
