from __future__ import annotations
import datetime as dt
import hashlib,json,uuid
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2];POLICY=ROOT/"contracts/synthetic-endpoint-telemetry-policy.json";DESTINATION=Path(__file__).with_name("endpoint-telemetry.json")
NAMESPACE=uuid.UUID("7b039e9e-5e9f-56bb-a1ae-1b5d12cc9c8c");SOURCES=("outlook-incidents.json","printer-incidents.json","scanner-incidents.json","windows-network-incidents.json")
CAPABILITIES={
 "outlook":["outlook.client_state.read","outlook.connectivity.read","outlook.sync_state.read","windows.event_summary.read","windows.resource_health.read"],
 "printer":["print.inventory.read","print.queue_metadata.read","print.spooler_state.read","print.port_reachability.read","windows.event_summary.read"],
 "scanner":["scan.inventory.read","scan.wia_state.read","scan.twain_metadata.read","scan.connectivity.read","windows.event_summary.read"],
 "windows":["network.adapter_state.read","network.ip_configuration.read","network.dns_resolution.read","network.route_state.read","windows.resource_health.read"]}
def digest(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def iso(base:dt.datetime,milliseconds:int)->str:return (base+dt.timedelta(milliseconds=milliseconds)).isoformat().replace("+00:00","Z")
def build()->dict[str,Any]:
 policy=json.loads(POLICY.read_text());cases=[]
 for source in SOURCES:
  domain="windows" if source.startswith("windows") else source.split("-")[0];cases.extend((domain,c) for c in json.loads((ROOT/"data/synthetic"/source).read_text())["cases"])
 packs=[];base=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
 for index,(domain,case) in enumerate(cases):
  correlation=str(uuid.uuid5(NAMESPACE,f"correlation:{policy['seed']}:{case['case_id']}"));results=[]
  for step,capability in enumerate(CAPABILITIES[domain]):
   status="timeout" if (index+step)%29==0 else "failure" if (index+step)%17==0 else "partial" if (index+step)%13==0 else "success"
   duration=5000 if status=="timeout" else 35+((case["seed"]+step*97)%1200);offset=index*6000+step*1000
   result_id=str(uuid.uuid5(NAMESPACE,f"result:{case['case_id']}:{capability}:{step}"));observed="fault_correlated" if step==0 else "baseline_observation"
   output={"schema":"typed_diagnostic_v1","observed_state":observed,"synthetic":True,"field_count":4,"content_included":False}
   error=None if status in {"success","partial"} else {"code":"SYNTHETIC_TIMEOUT" if status=="timeout" else "SYNTHETIC_DIAGNOSTIC_FAILURE","retryable":status=="timeout","safe_message":"The bounded synthetic diagnostic did not complete.","stack_trace_included":False}
   results.append({"result_id":result_id,"capability_id":capability,"status":status,"started_at":iso(base,offset),"completed_at":iso(base,offset+duration),"duration_ms":duration,"correlation_id":correlation,"incident_case_id":case["case_id"],"endpoint_id":case["endpoint"]["id"],"output":output,"redaction":{"applied":True,"fields_removed":["credentials","tokens","private_keys","content","personal_data"]},"error":error,"lineage":{"source":"synthetic_endpoint_agent","source_case_digest":digest(case),"sequence":step}})
  heartbeat={"cpu_percent":10+(index%70),"memory_percent":25+(index%60),"disk_free_percent":20+(index%65),"agent_connected":index%31!=0,"pending_restart":index%19==0}
  packs.append({"pack_id":str(uuid.uuid5(NAMESPACE,f"pack:{policy['seed']}:{case['case_id']}")),"tenant_id":policy["tenant_id"],"incident_case_id":case["case_id"],"incident_id":case["incident_id"],"domain":domain,"endpoint_id":case["endpoint"]["id"],"correlation_id":correlation,"captured_at":iso(base,index*6000),"heartbeat":heartbeat,"results":results,"pack_digest":digest({"heartbeat":heartbeat,"results":results}),"replay":{"generator_version":"1.0.0","master_seed":policy["seed"],"source_case_seed":case["seed"],"sequence":index}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":policy["seed"],"pack_count":len(packs),"result_count":sum(len(p["results"]) for p in packs),"packs":packs};payload["dataset_digest"]=digest(payload);return payload
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
