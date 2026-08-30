from __future__ import annotations
import hashlib,json,random,uuid
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"contracts/windows-network-support-catalog.json";NETWORK=ROOT/"data/synthetic/network-environment.json";ENDPOINTS=ROOT/"data/synthetic/endpoints.json";POLICY=ROOT/"contracts/synthetic-windows-network-incident-generator-policy.json"
DESTINATION=Path(__file__).with_name("windows-network-incidents.json");NAMESPACE=uuid.UUID("a4350d75-c976-527d-a9d1-c8601e6fc30d")
def digest(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def build()->dict[str,Any]:
 catalog=json.loads(CATALOG.read_text());network=json.loads(NETWORK.read_text());endpoints={e["id"]:e for e in json.loads(ENDPOINTS.read_text())["endpoints"]};policy=json.loads(POLICY.read_text());seed=policy["seed"]
 states=sorted(network["endpoint_states"],key=lambda x:x["hostname"]);functions=policy["business_functions"];cases=[]
 for incident_index,incident in enumerate(catalog["incidents"]):
  for variant in range(5):
   state=states[(incident_index+variant)%len(states)];endpoint=endpoints[state["endpoint_id"]];rng=random.Random(seed+incident_index*100+variant)
   cause=incident["hypotheses"][variant%len(incident["hypotheses"])];remediation=incident["remediations"][variant%len(incident["remediations"])]
   risk=remediation["risk"];status="escalated" if risk=="high" or cause in {"hardware_failure","security_policy_block","service_outage"} else "resolved";case_seed=rng.randrange(1_000_000,9_999_999);business_function=functions[(incident_index+variant)%len(functions)]
   case_id=str(uuid.uuid5(NAMESPACE,f"{seed}:{incident['id']}:{variant}:{state['endpoint_id']}"))
   evidence=[{"source":"endpoint_network_state","fact":f"adapter={state['adapter']['id']}","sensitive_values_redacted":True}]
   evidence.extend({"source":"bounded_diagnostic","fact":step,"result":"synthetic_match" if i==0 else "synthetic_observation","sensitive_values_redacted":True} for i,step in enumerate(incident["diagnostics"][:5]))
   device_state={"baseline_digest":digest({"network":state,"endpoint":endpoint}),"fault":cause,"synthetic":True,"adapter":state["adapter"],"dns":{"servers_count":len(state["dns"]["servers"]),"cache_state":state["dns"]["cache_state"]},"proxy":{"mode":state["proxy"]["mode"],"winhttp_aligned":state["proxy"]["winhttp_aligned"]},"vpn":{"profile":state["vpn"]["profile"],"connected":state["vpn"]["connected"]},"resource_health":endpoint["baseline_health"],"security_management":endpoint["security_posture"]["firewall"]}
   cases.append({"case_id":case_id,"seed":case_seed,"tenant_id":policy["tenant_id"],"endpoint":{"id":state["endpoint_id"],"hostname":state["hostname"],"operating_system":endpoint["operating_system"],"build":endpoint["build"]},"incident_id":incident["id"],"symptoms":list(dict.fromkeys(incident["signals"][:2]+[f"synthetic_{cause}"])),"clarifying_questions":incident["questions"],"device_state":device_state,"diagnostic_evidence":evidence,"relevant_knowledge":{"catalog_id":incident["id"],"source_class":"governed_windows_network_catalog"},"root_cause":cause,"safe_remediation":remediation["action"],"risk_level":risk,"required_approval":remediation["approval"],"rollback":remediation["rollback"],"post_remediation_state":"baseline_connectivity_restored" if status=="resolved" else "unchanged_pending_specialist","verification":{"layer_checks":["link","ip_configuration","gateway","dns","route","proxy_or_vpn","target_port"],"original_business_function":business_function,"business_function_success_required":True,"ping_or_dns_alone_sufficient":False,"employee_confirmation_required":True},"employee_response":"synthetic_business_function_confirmed" if status=="resolved" else "synthetic_escalation_acknowledged","expected_final_status":status,"timeline":[{"offset_seconds":0,"event":"connectivity_issue_reported"},{"offset_seconds":10,"event":"read_only_layer_isolation_completed"},{"offset_seconds":20,"event":"approval_or_escalation_recorded"},{"offset_seconds":35,"event":"bounded_remediation_result_recorded"},{"offset_seconds":50,"event":"original_business_function_verified"}],"replay":{"generator_version":"1.0.0","master_seed":seed,"case_seed":case_seed,"variant":variant}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":seed,"case_count":len(cases),"cases":cases};payload["dataset_digest"]=digest(payload);return payload
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
