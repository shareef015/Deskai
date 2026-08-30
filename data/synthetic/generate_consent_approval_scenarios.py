from __future__ import annotations
import datetime as dt
import hashlib,json,uuid
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2];POLICY=ROOT/"contracts/synthetic-consent-approval-policy.json";ENDPOINTS=ROOT/"data/synthetic/endpoints.json";DESTINATION=Path(__file__).with_name("consent-approval-scenarios.json")
NAMESPACE=uuid.UUID("20605432-8a5a-5512-964c-52d3b94ed577");SOURCES=("outlook-incidents.json","printer-incidents.json","scanner-incidents.json","windows-network-incidents.json")
OUTCOMES=("authorized","consent_declined","consent_expired","consent_revoked","device_mismatch","incident_mismatch","tenant_mismatch","unauthorized_approver","self_approval_denied","ai_authority_denied")
APPROVERS={"read_only":("usr-001","employee"),"low":("usr-017","service_desk_engineer"),"medium":("usr-019","remediation_approver"),"high":("usr-020","endpoint_administrator")}
def digest(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def iso(value:dt.datetime)->str:return value.isoformat().replace("+00:00","Z")
def build()->dict[str,Any]:
 policy=json.loads(POLICY.read_text());endpoints={e["id"]:e for e in json.loads(ENDPOINTS.read_text())["endpoints"]};cases=[]
 for source in SOURCES:cases.extend(json.loads((ROOT/"data/synthetic"/source).read_text())["cases"])
 scenarios=[];base=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
 for index,case in enumerate(cases):
  outcome=OUTCOMES[index%len(OUTCOMES)];endpoint=endpoints[case["endpoint"]["id"]];employee=endpoint["primary_user_id"];issued=base+dt.timedelta(minutes=index);expires=issued+dt.timedelta(minutes=policy["consent_ttl_minutes"]);evaluated=issued+dt.timedelta(minutes=5)
  consent_status="granted";consent_device=endpoint["id"];consent_incident=case["case_id"];consent_tenant=policy["tenant_id"]
  if outcome=="consent_declined":consent_status="declined"
  elif outcome=="consent_expired":evaluated=expires+dt.timedelta(seconds=1)
  elif outcome=="consent_revoked":consent_status="revoked"
  elif outcome=="device_mismatch":consent_device="mismatched-device"
  elif outcome=="incident_mismatch":consent_incident="mismatched-incident"
  elif outcome=="tenant_mismatch":consent_tenant="mismatched-tenant"
  approver_id,approver_role=APPROVERS[case["risk_level"]]
  if outcome=="unauthorized_approver":approver_id,approver_role="usr-025","auditor"
  elif outcome=="self_approval_denied":approver_id,approver_role="usr-016","service_desk_engineer"
  elif outcome=="ai_authority_denied":approver_id,approver_role="svc-ai","ai_service"
  diagnostic_authorized=outcome in {"authorized","unauthorized_approver","self_approval_denied","ai_authority_denied"}
  remediation_authorized=outcome=="authorized";approval_status="approved" if outcome=="authorized" else "rejected" if outcome in {"unauthorized_approver","self_approval_denied","ai_authority_denied"} else "not_evaluated"
  scenario_id=str(uuid.uuid5(NAMESPACE,f"{policy['seed']}:{case['case_id']}:{outcome}"));session_id=str(uuid.uuid5(NAMESPACE,f"session:{case['case_id']}"))
  consent={"consent_id":str(uuid.uuid5(NAMESPACE,f"consent:{scenario_id}")),"tenant_id":consent_tenant,"employee_id":employee,"device_id":consent_device,"incident_id":consent_incident,"session_id":session_id,"purpose":"read_only_diagnostics","capabilities":["endpoint.read_diagnostics"],"status":consent_status,"issued_at":iso(issued),"expires_at":iso(expires),"revoked_at":iso(issued+dt.timedelta(minutes=2)) if consent_status=="revoked" else None}
  approval={"approval_id":str(uuid.uuid5(NAMESPACE,f"approval:{scenario_id}")),"tenant_id":policy["tenant_id"],"incident_id":case["case_id"],"device_id":endpoint["id"],"action":case["safe_remediation"],"risk_level":case["risk_level"],"requester_id":"usr-016","approver_id":approver_id,"approver_role":approver_role,"status":approval_status,"issued_at":iso(issued+dt.timedelta(minutes=6)),"expires_at":iso(issued+dt.timedelta(minutes=policy["approval_ttl_minutes"]+6)),"pre_state_digest":case["device_state"]["baseline_digest"],"rollback":case["rollback"]}
  scenarios.append({"scenario_id":scenario_id,"seed":case["seed"],"tenant_id":policy["tenant_id"],"incident_case_id":case["case_id"],"endpoint_id":endpoint["id"],"employee_id":employee,"outcome":outcome,"consent":consent,"approval":approval,"evaluation":{"evaluated_at":iso(evaluated),"diagnostic_authorized":diagnostic_authorized,"remediation_authorized":remediation_authorized,"execution_permitted":remediation_authorized,"reason":outcome,"fail_closed":outcome!="authorized","audit_event_ids":[str(uuid.uuid5(NAMESPACE,f"audit:{scenario_id}:consent")),str(uuid.uuid5(NAMESPACE,f"audit:{scenario_id}:approval"))]},"replay":{"generator_version":"1.0.0","master_seed":policy["seed"],"source_case_seed":case["seed"],"sequence":index}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":policy["seed"],"scenario_count":len(scenarios),"scenarios":scenarios};payload["dataset_digest"]=digest(payload);return payload
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
