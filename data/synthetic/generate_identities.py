from __future__ import annotations
import json
from pathlib import Path
from uuid import UUID, uuid5

ROOT=Path(__file__).resolve().parents[2]
WORKFORCE=ROOT/"data/synthetic/workforce.json"
DESTINATION=Path(__file__).with_name("identities.json")
NAMESPACE=UUID("589b9747-d68c-51c7-bfd2-904de94f54ea")
TENANT_OBJECT_ID=str(uuid5(NAMESPACE,"tenant-demo-kw"))

def build() -> dict:
    workforce=json.loads(WORKFORCE.read_text(encoding="utf-8")); identities=[]
    for person in workforce["people"]:
        object_id=str(uuid5(NAMESPACE,person["id"]))
        identities.append({"persona_id":person["id"],"oid":object_id,"sub":object_id,"tid":TENANT_OBJECT_ID,"name":person["display_name"],"preferred_username":f"{person['id']}@demo.invalid","roles":[person["role"]],"deskpilot_tenant_id":workforce["tenant_id"],"account_enabled":True})
    return {"schema_version":"1.0.0","synthetic_only":True,"seed":43001,"issuer":"https://synthetic.identity.invalid/tenant-demo-kw/v2.0","audience":"deskpilot-demo","tenant_object_id":TENANT_OBJECT_ID,"identities":identities}

def canonical_bytes() -> bytes:
    return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()

if __name__=="__main__":
    DESTINATION.write_bytes(canonical_bytes()); print(DESTINATION)
