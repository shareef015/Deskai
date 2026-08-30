from __future__ import annotations
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path: str)->dict: return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate()->list[str]:
    policy=load("contracts/synthetic-identity-policy.json"); fixture=load(policy["fixture"]); workforce=load("data/synthetic/workforce.json"); errors=[]
    identities=fixture.get("identities",[]); persona_ids={p["id"] for p in workforce["people"]}
    if not fixture.get("synthetic_only") or fixture.get("seed")!=policy["seed"]: errors.append("identity seed mismatch")
    if {i["persona_id"] for i in identities}!=persona_ids: errors.append("identity coverage mismatch")
    if len({i["oid"] for i in identities})!=len(identities): errors.append("duplicate synthetic object id")
    if any(not i["preferred_username"].endswith("@demo.invalid") for i in identities): errors.append("non-synthetic login domain")
    if any(i["roles"] != [next(p["role"] for p in workforce["people"] if p["id"]==i["persona_id"])] for i in identities): errors.append("role claim mismatch")
    login=policy["demo_login"]
    if login["production_enabled"] or login["passwords_used"] or login["issues_real_oidc_tokens"]: errors.append("unsafe demo login mode")
    spec=importlib.util.spec_from_file_location("identity_generator",ROOT/"data/synthetic/generate_identities.py"); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if (ROOT/policy["fixture"]).read_bytes()!=module.canonical_bytes(): errors.append("identity replay mismatch")
    source=(ROOT/"services/api/src/deskpilot_api/auth/demo_login.py").read_text()
    for token in ('environment in {"development", "test"}',"synthetic_mode and trusted_origin","secrets.token_urlsafe(32)"):
        if token not in source: errors.append(f"demo login control missing: {token}")
    return errors

if __name__=="__main__":
    failures=validate()
    if failures: raise SystemExit("\n".join(failures))
    print("synthetic identity and demo login validation passed")
