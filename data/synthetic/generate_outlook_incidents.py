from __future__ import annotations
import hashlib,json,random,uuid
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"contracts/outlook-support-catalog.json";ENVIRONMENT=ROOT/"data/synthetic/outlook-environment.json";POLICY=ROOT/"contracts/synthetic-outlook-incident-generator-policy.json"
DESTINATION=Path(__file__).with_name("outlook-incidents.json");NAMESPACE=uuid.UUID("e24da684-f271-5b2a-969c-fb242ed4d6c5")

def digest(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def build()->dict[str,Any]:
 catalog=json.loads(CATALOG.read_text());environment=json.loads(ENVIRONMENT.read_text());policy=json.loads(POLICY.read_text());seed=policy["seed"]
 clients=sorted(environment["clients"],key=lambda item:item["hostname"]);cases=[]
 for incident_index,incident in enumerate(catalog["incidents"]):
  eligible=[c for c in clients if f"{c['client']['variant']}_outlook" in incident["clients"]]
  for variant in range(5):
   endpoint=eligible[(incident_index+variant)%len(eligible)];rng=random.Random(seed+incident_index*100+variant)
   cause=incident["hypotheses"][variant%len(incident["hypotheses"])];remediation=incident["remediations"][variant%len(incident["remediations"])] if incident["remediations"] else None
   risk=remediation["risk"] if remediation else "read_only";approval=remediation["approval"] if remediation else "not_required";status="escalated" if risk=="high" or cause=="service_outage" else "resolved"
   case_seed=rng.randrange(1_000_000,9_999_999);case_id=str(uuid.uuid5(NAMESPACE,f"{seed}:{incident['id']}:{variant}:{endpoint['endpoint_id']}"))
   evidence=[{"source":"endpoint_state","fact":f"client={endpoint['client']['variant']}","content_included":False}]
   evidence.extend({"source":"diagnostic","fact":diagnostic,"result":"synthetic_match" if i==0 else "synthetic_observation","content_included":False} for i,diagnostic in enumerate(incident["diagnostics"][:3]))
   cases.append({"case_id":case_id,"seed":case_seed,"tenant_id":policy["tenant_id"],"endpoint":{"id":endpoint["endpoint_id"],"hostname":endpoint["hostname"]},"client":endpoint["client"],"incident_id":incident["id"],"symptoms":list(dict.fromkeys(incident["signals"][:2]+[f"synthetic_{cause}"])),"clarifying_questions":incident["questions"],"device_state":{"baseline_digest":digest(endpoint),"fault":cause,"synthetic":True},"diagnostic_evidence":evidence,"relevant_knowledge":{"catalog_id":incident["id"],"source_class":"governed_outlook_catalog"},"root_cause":cause,"safe_remediation":remediation["action"] if remediation else "observe_and_escalate","risk_level":risk,"required_approval":approval,"rollback":remediation["rollback"] if remediation else "not_required","post_remediation_state":"baseline_restored" if status=="resolved" else "unchanged_pending_admin","verification":incident["verification"],"employee_response":"synthetic_confirmation" if status=="resolved" else "synthetic_escalation_acknowledged","expected_final_status":status,"timeline":[{"offset_seconds":0,"event":"incident_reported"},{"offset_seconds":15,"event":"diagnostics_completed"},{"offset_seconds":30,"event":"approval_or_escalation_recorded"},{"offset_seconds":45,"event":"verification_completed"}],"replay":{"generator_version":"1.0.0","master_seed":seed,"case_seed":case_seed,"variant":variant}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":seed,"case_count":len(cases),"cases":cases};payload["dataset_digest"]=digest(payload);return payload

def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
