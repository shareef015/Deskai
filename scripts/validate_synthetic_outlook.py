from __future__ import annotations
import importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path:str)->dict: return json.loads((ROOT/path).read_text(encoding="utf-8"))
def validate()->list[str]:
    policy=load("contracts/synthetic-outlook-environment-policy.json"); fixture=load(policy["fixture"]); endpoints=load("data/synthetic/endpoints.json")["endpoints"]; errors=[]
    clients=fixture.get("clients",[]); mailboxes=fixture.get("mailboxes",[])
    if not fixture.get("synthetic_only") or fixture.get("seed")!=policy["seed"]: errors.append("Outlook seed mismatch")
    if {c["endpoint_id"] for c in clients}!={e["id"] for e in endpoints} or len(clients)!=10: errors.append("Outlook endpoint coverage mismatch")
    if {c["client"]["variant"] for c in clients}!={"classic","new"}: errors.append("classic/new client coverage missing")
    if any(not m["primary_address"].endswith("@demo.invalid") or m["content_included"] for m in mailboxes): errors.append("mailbox privacy boundary violated")
    if any(c["authentication"]["token_material_present"] or c["authentication"]["mfa_secret_present"] or not c["cache"]["metadata_only"] for c in clients): errors.append("secret or mailbox cache content present")
    if any(c["active_faults"] or c["tenant_id"]!=policy["tenant_id"] for c in clients): errors.append("baseline Outlook state invalid")
    if set(policy["fault_types"])!={f["type"] for f in fixture.get("fault_catalog",[])}: errors.append("Outlook fault catalog mismatch")
    if any("restore_value" not in f for f in fixture.get("fault_catalog",[])): errors.append("Outlook fault lacks rollback")
    spec=importlib.util.spec_from_file_location("outlook_generator",ROOT/"data/synthetic/generate_outlook_environment.py"); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if (ROOT/policy["fixture"]).read_bytes()!=module.canonical_bytes(): errors.append("Outlook replay mismatch")
    return errors
if __name__=="__main__":
    failures=validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic Outlook environment validation passed")
