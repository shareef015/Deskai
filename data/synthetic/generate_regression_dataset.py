from __future__ import annotations
import hashlib,json,uuid
from collections import Counter
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2];POLICY=ROOT/"contracts/regression-dataset-policy.json";DESTINATION=Path(__file__).with_name("regression-cases.json");MANIFEST=Path(__file__).with_name("regression-replay-manifest.json")
NAMESPACE=uuid.UUID("6d417416-06dd-58f6-adbd-4869d5c8c88a")
SOURCES={"outlook":"outlook-incidents.json","printer":"printer-incidents.json","scanner":"scanner-incidents.json","windows_network":"windows-network-incidents.json"};CLASSES=("normal","failure","security","edge")
def digest(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def load_index(filename:str,key:str,id_field:str)->dict[str,dict[str,Any]]:return {x[id_field]:x for x in json.loads((ROOT/"data/synthetic"/filename).read_text())[key]}
def build()->tuple[dict[str,Any],dict[str,Any]]:
 policy=json.loads(POLICY.read_text());conversations=load_index("support-conversations.json","conversations","incident_case_id");telemetry=load_index("endpoint-telemetry.json","packs","incident_case_id");authorizations=load_index("consent-approval-scenarios.json","scenarios","incident_case_id");remediations=load_index("remediation-scenarios.json","scenarios","incident_case_id");records=[]
 global_index=0
 for domain,filename in SOURCES.items():
  source_cases=json.loads((ROOT/"data/synthetic"/filename).read_text())["cases"]
  for domain_index in range(policy["domain_case_counts"][domain]):
   source_index=domain_index%len(source_cases);source=source_cases[source_index];replica=domain_index//len(source_cases);scenario_class=CLASSES[global_index%len(CLASSES)];split="release_gate" if source_index%5==0 else "regression_core"
   conversation=conversations[source["case_id"]];pack=telemetry[source["case_id"]];authorization=authorizations[source["case_id"]];remediation=remediations[source["case_id"]]
   regression_id=str(uuid.uuid5(NAMESPACE,f"{policy['seed']}:{domain}:{source['case_id']}:{replica}:{scenario_class}"));case_seed=int(digest(regression_id)[:8],16)
   records.append({"regression_id":regression_id,"seed":case_seed,"tenant_id":policy["tenant_id"],"domain":domain,"scenario_class":scenario_class,"split":split,"source_case_id":source["case_id"],"incident_id":source["incident_id"],"endpoint_id":source["endpoint"]["id"],"input":{"symptoms":source["symptoms"],"clarifying_questions":source["clarifying_questions"],"device_state":source["device_state"],"diagnostic_evidence":source["diagnostic_evidence"],"relevant_knowledge":source["relevant_knowledge"]},"expected":{"root_cause":source["root_cause"],"safe_remediation":source["safe_remediation"],"risk_level":source["risk_level"],"required_approval":source["required_approval"],"rollback":source["rollback"],"post_remediation_state":source["post_remediation_state"],"verification":source["verification"],"employee_response":source["employee_response"],"final_status":source["expected_final_status"],"consent_outcome":authorization["outcome"],"execution_outcome":remediation["outcome"],"execution_terminal_state":remediation["final_state"]["terminal_state"]},"artifact_refs":{"conversation_id":conversation["conversation_id"],"telemetry_pack_id":pack["pack_id"],"authorization_scenario_id":authorization["scenario_id"],"remediation_scenario_id":remediation["scenario_id"],"telemetry_correlation_id":pack["correlation_id"]},"source_digest":digest(source),"replay":{"generator_version":"1.0.0","master_seed":policy["seed"],"source_seed":source["seed"],"source_index":source_index,"replica":replica,"sequence":global_index}});global_index+=1
 dataset={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":policy["seed"],"case_count":len(records),"cases":records};dataset["dataset_digest"]=digest(dataset)
 domains=Counter(r["domain"] for r in records);classes=Counter(r["scenario_class"] for r in records);splits=Counter(r["split"] for r in records);incidents=sorted({r["incident_id"] for r in records});endpoints=sorted({r["endpoint_id"] for r in records})
 manifest={"schema_version":"1.0.0","synthetic_only":True,"seed":policy["seed"],"dataset_file":DESTINATION.name,"dataset_digest":dataset["dataset_digest"],"case_count":len(records),"domain_counts":dict(sorted(domains.items())),"scenario_class_counts":dict(sorted(classes.items())),"split_counts":dict(sorted(splits.items())),"incident_ids":incidents,"endpoint_ids":endpoints,"source_group_split":{r["source_case_id"]:r["split"] for r in records},"replay_command":"python data/synthetic/generate_regression_dataset.py"};manifest["manifest_digest"]=digest(manifest);return dataset,manifest
def canonical_dataset_bytes()->bytes:return (json.dumps(build()[0],sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def canonical_manifest_bytes()->bytes:return (json.dumps(build()[1],sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_dataset_bytes());MANIFEST.write_bytes(canonical_manifest_bytes());print(DESTINATION);print(MANIFEST)
