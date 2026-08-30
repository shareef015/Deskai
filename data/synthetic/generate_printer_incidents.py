from __future__ import annotations
import hashlib,json,random,uuid
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"contracts/printer-support-catalog.json";ENVIRONMENT=ROOT/"data/synthetic/print-scan-environment.json";POLICY=ROOT/"contracts/synthetic-printer-incident-generator-policy.json"
DESTINATION=Path(__file__).with_name("printer-incidents.json");NAMESPACE=uuid.UUID("92c8773a-f01f-5bb8-9aaa-9a5d78ad5bf8")
def digest(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def build()->dict[str,Any]:
 catalog=json.loads(CATALOG.read_text());env=json.loads(ENVIRONMENT.read_text());policy=json.loads(POLICY.read_text());seed=policy["seed"]
 printers={p["id"]:p for p in env["printers"]};servers={s["id"]:s for s in env["print_servers"]};mappings=sorted(env["endpoint_mappings"],key=lambda x:x["hostname"]);cases=[]
 for incident_index,incident in enumerate(catalog["incidents"]):
  for variant in range(5):
   mapping=mappings[(incident_index+variant)%len(mappings)];printer=printers[mapping["printer_ids"][variant%len(mapping["printer_ids"])]];server=servers.get(printer.get("server_id"));rng=random.Random(seed+incident_index*100+variant)
   cause=incident["hypotheses"][variant%len(incident["hypotheses"])];remediation=incident["remediations"][variant%len(incident["remediations"])]
   risk=remediation["risk"];status="escalated" if risk=="high" or cause in {"mechanical_failure","electrical_hazard","consumable_empty"} else "resolved";case_seed=rng.randrange(1_000_000,9_999_999)
   case_id=str(uuid.uuid5(NAMESPACE,f"{seed}:{incident['id']}:{variant}:{mapping['endpoint_id']}:{printer['id']}"))
   evidence=[{"source":"windows_printer_inventory","fact":f"printer={printer['id']}","content_included":False}]
   evidence.extend({"source":"diagnostic","fact":step,"result":"synthetic_match" if i==0 else "synthetic_observation","content_included":False} for i,step in enumerate(incident["diagnostics"][:4]))
   topology={"connection":printer["connection"],"queue":printer["queue"],"port":printer["port"],"print_server":{"id":server["id"],"hostname":server["hostname"]} if server else None}
   cases.append({"case_id":case_id,"seed":case_seed,"tenant_id":policy["tenant_id"],"endpoint":{"id":mapping["endpoint_id"],"hostname":mapping["hostname"]},"printer":{"id":printer["id"],"name":printer["name"],"location_id":printer["location_id"]},"topology":topology,"incident_id":incident["id"],"symptoms":list(dict.fromkeys(incident["signals"][:2]+[f"synthetic_{cause}"])),"clarifying_questions":incident["questions"],"device_state":{"baseline_digest":digest({"mapping":mapping,"printer":printer,"server":server}),"fault":cause,"synthetic":True,"queue_metadata_only":True},"diagnostic_evidence":evidence,"relevant_knowledge":{"catalog_id":incident["id"],"source_class":"governed_printer_catalog"},"root_cause":cause,"safe_remediation":remediation["action"],"risk_level":risk,"required_approval":remediation["approval"],"rollback":remediation["rollback"],"post_remediation_state":"ready_and_queue_clear" if status=="resolved" else "unchanged_pending_specialist","verification":{"catalog_checks":incident["verification"],"test_print":"synthetic_test_page","job_completed_required":True,"physical_output_confirmation_required":True},"employee_response":"synthetic_physical_output_confirmed" if status=="resolved" else "synthetic_escalation_acknowledged","expected_final_status":status,"timeline":[{"offset_seconds":0,"event":"printer_issue_reported"},{"offset_seconds":12,"event":"topology_and_queue_inspected"},{"offset_seconds":24,"event":"approval_or_escalation_recorded"},{"offset_seconds":36,"event":"synthetic_test_page_submitted"},{"offset_seconds":48,"event":"physical_output_confirmation_recorded"}],"replay":{"generator_version":"1.0.0","master_seed":seed,"case_seed":case_seed,"variant":variant}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":seed,"case_count":len(cases),"cases":cases};payload["dataset_digest"]=digest(payload);return payload
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
