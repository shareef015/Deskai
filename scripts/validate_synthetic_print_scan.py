from __future__ import annotations
import importlib.util, ipaddress, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p:str)->dict:return json.loads((ROOT/p).read_text())
def validate()->list[str]:
 p=load("contracts/synthetic-print-scan-policy.json"); f=load(p["fixture"]); endpoints=load("data/synthetic/endpoints.json")["endpoints"]; errors=[]
 if not f.get("synthetic_only") or f.get("seed")!=p["seed"]:errors.append("print/scan seed mismatch")
 for key in ("printers","scanners","print_servers"):
  if len(f.get(key,[]))!=p["counts"][key]:errors.append(f"{key} count mismatch")
 if {m["endpoint_id"] for m in f["endpoint_mappings"]}!={e["id"] for e in endpoints}:errors.append("endpoint mapping coverage mismatch")
 if any(not ipaddress.ip_address(x["port"]["address"]).is_private for x in f["printers"]):errors.append("non-private printer address")
 if any(not x["driver"]["signed"] for x in f["printers"]) or any(not x["wia"]["signed"] for x in f["scanners"]):errors.append("unsigned driver")
 if any("wia" not in x or "twain" not in x for x in f["scanners"]):errors.append("WIA/TWAIN separation missing")
 if set(p["fault_types"])!={x["type"] for x in f["fault_catalog"]} or any("restore_value" not in x for x in f["fault_catalog"]):errors.append("fault/rollback mismatch")
 if not f["verification"]["test_print"]["physical_confirmation_required"] or f["verification"]["test_scan"]["content_inspection"]:errors.append("verification privacy invariant missing")
 spec=importlib.util.spec_from_file_location("psgen",ROOT/"data/synthetic/generate_print_scan_environment.py");assert spec and spec.loader;mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 if (ROOT/p["fixture"]).read_bytes()!=mod.canonical_bytes():errors.append("print/scan replay mismatch")
 return errors
if __name__=="__main__":
 e=validate()
 if e:raise SystemExit("\n".join(e))
 print("synthetic print and scan environment validation passed")
