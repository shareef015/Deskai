from __future__ import annotations
import hashlib,json,random,uuid
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"contracts/scanner-support-catalog.json";ENVIRONMENT=ROOT/"data/synthetic/print-scan-environment.json";POLICY=ROOT/"contracts/synthetic-scanner-incident-generator-policy.json"
DESTINATION=Path(__file__).with_name("scanner-incidents.json");NAMESPACE=uuid.UUID("52242f9c-7ebf-52cb-ae31-3bf3ea98db17")
def digest(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def build()->dict[str,Any]:
 catalog=json.loads(CATALOG.read_text());env=json.loads(ENVIRONMENT.read_text());policy=json.loads(POLICY.read_text());seed=policy["seed"]
 scanners={s["id"]:s for s in env["scanners"]};printers={p["id"]:p for p in env["printers"]};mappings=sorted(env["endpoint_mappings"],key=lambda x:x["hostname"]);cases=[]
 for incident_index,incident in enumerate(catalog["incidents"]):
  for variant in range(5):
   mapping=mappings[(incident_index+variant)%len(mappings)];scanner=scanners[mapping["scanner_ids"][variant%len(mapping["scanner_ids"])] ];printer=printers.get(scanner.get("printer_id"));rng=random.Random(seed+incident_index*100+variant)
   cause=incident["hypotheses"][variant%len(incident["hypotheses"])];remediation=incident["remediations"][variant%len(incident["remediations"])]
   risk=remediation["risk"];status="escalated" if risk=="high" or cause in {"mechanical_failure","electrical_hazard","hardware_failure"} else "resolved";case_seed=rng.randrange(1_000_000,9_999_999)
   case_id=str(uuid.uuid5(NAMESPACE,f"{seed}:{incident['id']}:{variant}:{mapping['endpoint_id']}:{scanner['id']}"))
   evidence=[{"source":"windows_scanner_inventory","fact":f"scanner={scanner['id']}","content_included":False}]
   evidence.extend({"source":"diagnostic","fact":step,"result":"synthetic_match" if i==0 else "synthetic_observation","content_included":False} for i,step in enumerate(incident["diagnostics"][:4]))
   topology={"connection":scanner["connection"],"address":scanner["address"],"type":scanner["type"],"mfp_printer_id":printer["id"] if printer else None,"wia_driver":scanner["wia"]["driver"],"twain_source":scanner["twain"]["source"]}
   cases.append({"case_id":case_id,"seed":case_seed,"tenant_id":policy["tenant_id"],"endpoint":{"id":mapping["endpoint_id"],"hostname":mapping["hostname"]},"scanner":{"id":scanner["id"],"name":scanner["name"],"location_id":scanner["location_id"]},"topology":topology,"incident_id":incident["id"],"symptoms":list(dict.fromkeys(incident["signals"][:2]+[f"synthetic_{cause}"])),"clarifying_questions":incident["questions"],"device_state":{"baseline_digest":digest({"mapping":mapping,"scanner":scanner,"printer":printer}),"fault":cause,"synthetic":True,"wia_service":mapping["wia_service"]},"diagnostic_evidence":evidence,"relevant_knowledge":{"catalog_id":incident["id"],"source_class":"governed_scanner_catalog"},"root_cause":cause,"safe_remediation":remediation["action"],"risk_level":risk,"required_approval":remediation["approval"],"rollback":remediation["rollback"],"post_remediation_state":"ready_and_application_accessible" if status=="resolved" else "unchanged_pending_specialist","verification":{"catalog_checks":incident["verification"],"source":"approved_synthetic_sheet","test_scan_artifact":{"id":f"artifact-{case_id[:12]}","content_inspected":False,"retention":"temporary","accessible_required":True},"employee_confirmation_required":True},"employee_response":"synthetic_scan_artifact_confirmed" if status=="resolved" else "synthetic_escalation_acknowledged","expected_final_status":status,"timeline":[{"offset_seconds":0,"event":"scanner_issue_reported"},{"offset_seconds":12,"event":"wia_twain_and_topology_inspected"},{"offset_seconds":24,"event":"approval_or_escalation_recorded"},{"offset_seconds":36,"event":"synthetic_test_scan_created"},{"offset_seconds":48,"event":"artifact_and_employee_confirmation_recorded"}],"replay":{"generator_version":"1.0.0","master_seed":seed,"case_seed":case_seed,"variant":variant}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":seed,"case_count":len(cases),"cases":cases};payload["dataset_digest"]=digest(payload);return payload
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
