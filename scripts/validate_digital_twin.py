from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p:str)->dict:return json.loads((ROOT/p).read_text())
def validate()->list[str]:
 p=load("contracts/digital-twin-policy.json");m=load(p["manifest"]);errors=[]
 if not m.get("synthetic_only") or m.get("seed")!=p["seed"]:errors.append("digital twin seed mismatch")
 if [x["name"] for x in m["components"]]!=p["components"]:errors.append("component manifest mismatch")
 for entry in m["components"]:
  raw=(ROOT/"data/synthetic"/entry["name"]).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=entry["sha256"]:errors.append(f"component digest mismatch: {entry['name']}")
  if entry["tenant_id"]!=p["tenant_id"]:errors.append(f"tenant mismatch: {entry['name']}")
 endpoints={x["id"] for x in load("data/synthetic/endpoints.json")["endpoints"]}
 for file_name,key in (("device-inventory.json","inventories"),("network-environment.json","endpoint_states"),("outlook-environment.json","clients"),("print-scan-environment.json","endpoint_mappings")):
  if {x["endpoint_id"] for x in load("data/synthetic/"+file_name)[key]}!=endpoints:errors.append(f"cross-domain endpoint mismatch: {file_name}")
 spec=importlib.util.spec_from_file_location("manifest_generator",ROOT/"data/synthetic/generate_digital_twin_manifest.py");assert spec and spec.loader;mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 if (ROOT/p["manifest"]).read_bytes()!=mod.canonical_bytes():errors.append("manifest replay mismatch")
 source=(ROOT/"services/api/src/deskpilot_api/synthetic/digital_twin.py").read_text()
 for token in ("expected_version!=self._version","copy.deepcopy","maximum" if False else "len(sequence)>100"):
  if token not in source:errors.append(f"runtime invariant missing: {token}")
 return errors
if __name__=="__main__":
 e=validate()
 if e:raise SystemExit("\n".join(e))
 print("digital twin and deterministic replay validation passed")
