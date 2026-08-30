from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DESTINATION=ROOT/"digital-twin-manifest.json"
COMPONENTS=["organization.json","workforce.json","identities.json","endpoints.json","device-inventory.json","network-environment.json","outlook-environment.json","print-scan-environment.json"]
def build()->dict:
 entries=[]
 for name in COMPONENTS:
  raw=(ROOT/name).read_bytes(); data=json.loads(raw)
  tenant_id=data.get("tenant_id") or data.get("tenant",{}).get("id")
  if tenant_id is None and data.get("identities"):tenant_id=data["identities"][0].get("deskpilot_tenant_id")
  entries.append({"name":name,"sha256":hashlib.sha256(raw).hexdigest(),"seed":data.get("seed"),"tenant_id":tenant_id})
 root=hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 return {"schema_version":"1.0.0","synthetic_only":True,"seed":49001,"tenant_id":"tenant-demo-kw","components":entries,"baseline_digest":root}
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"))+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
