from __future__ import annotations
import hashlib,json,uuid
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2];POLICY=ROOT/"contracts/synthetic-conversation-generator-policy.json";ENDPOINTS=ROOT/"data/synthetic/endpoints.json"
DESTINATION=Path(__file__).with_name("support-conversations.json");NAMESPACE=uuid.UUID("1a8a79de-f41c-5386-979e-31ae280a20ba")
SOURCES=("outlook-incidents.json","printer-incidents.json","scanner-incidents.json","windows-network-incidents.json")
def digest(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def greeting(seed:int)->str:
 hour=seed%24;period="morning" if hour<12 else "afternoon" if hour<17 else "evening";return f"Good {period}. How can I help you?"
def turn(sequence:int,role:str,state:str,text:str,decision:str|None=None)->dict[str,Any]:
 item={"sequence":sequence,"offset_seconds":sequence*6,"role":role,"state":state,"text":text};
 if decision:item["decision"]=decision
 return item
def build()->dict[str,Any]:
 policy=json.loads(POLICY.read_text());endpoints={e["id"]:e for e in json.loads(ENDPOINTS.read_text())["endpoints"]};conversations=[]
 incidents=[]
 for source in SOURCES:
  domain=source.split("-")[0] if not source.startswith("windows") else "windows_network"
  incidents.extend((domain,case) for case in json.loads((ROOT/"data/synthetic"/source).read_text())["cases"])
 for index,(domain,case) in enumerate(incidents):
  endpoint=endpoints[case["endpoint"]["id"]];branch=index%5;conversation_id=str(uuid.uuid5(NAMESPACE,f"{policy['seed']}:{case['case_id']}:{branch}"));seq=0;turns=[]
  def add(role:str,state:str,text:str,decision:str|None=None)->None:
   nonlocal seq;turns.append(turn(seq,role,state,text,decision));seq+=1
  add("assistant","greeting",greeting(case["seed"]));add("employee","intake",f"I need help with synthetic symptom {case['symptoms'][0]} on {case['endpoint']['hostname']}.")
  question=case["clarifying_questions"][0];add("assistant","clarifying",question);add("employee","clarifying",f"Synthetic answer for {case['root_cause']}; no private content included.")
  add("assistant","classified",f"I classified this as {case['incident_id']} using the governed support catalogue.");add("assistant","device_resolved",f"I found your registered synthetic device {case['endpoint']['hostname']}.")
  add("assistant","awaiting_diagnostic_consent","May I connect for this incident and run read-only diagnostics? This consent applies only to this incident.")
  if branch==1:
   add("employee","awaiting_diagnostic_consent","Do not connect. Please guide me instead.","declined");add("assistant","guided_support","Diagnostics were not started. I will provide guided support or arrange escalation.");terminal="guided_support";consent="declined";approval="not_requested";confirmation="not_requested"
  else:
   add("employee","awaiting_diagnostic_consent","Allow read-only diagnostics for this incident.","granted");consent="granted"
   add("assistant","diagnosing","Read-only synthetic diagnostics are complete; no secrets or content were collected.");add("assistant","evidence_review",f"The evidence supports synthetic root cause {case['root_cause']}.")
   requires_approval=case["risk_level"]!="read_only" or case["required_approval"]!="not_required"
   if requires_approval:
    add("assistant","awaiting_remediation_approval",f"May I perform {case['safe_remediation']}? Risk is {case['risk_level']}; rollback is {case['rollback']}.")
    if branch==2:
     add("employee","awaiting_remediation_approval","Reject the remediation. Escalate this incident.","rejected");add("assistant","escalated","No remediation was run. The evidence package was escalated.");terminal="escalated";approval="rejected";confirmation="acknowledged"
    else:
     add("employee","awaiting_remediation_approval","Approve this specific remediation.","approved");approval="approved";add("assistant","remediating","The approved synthetic remediation completed and retained its rollback record.");terminal=""
   else:approval="not_required";add("assistant","remediating","The policy-authorized read-only outcome was recorded.");terminal=""
   if not terminal:
    add("assistant","technical_verification",f"Technical verification completed: {case['verification'] if isinstance(case['verification'],list) else 'domain-specific verification'}.")
    add("assistant","awaiting_employee_confirmation","Is the original problem fixed now?")
    if branch==4:
     add("employee","awaiting_employee_confirmation","The original problem is still present.","not_fixed");add("assistant","monitoring","The incident remains open for escalation and further evidence.");terminal="monitoring";confirmation="not_fixed"
    elif case["expected_final_status"]=="escalated":
     add("employee","awaiting_employee_confirmation","I understand that specialist escalation is required.","acknowledged");add("assistant","escalated","The evidence and approval boundary were recorded for the specialist.");terminal="escalated";confirmation="acknowledged"
    else:
     add("employee","awaiting_employee_confirmation","Yes, the original problem is fixed.","confirmed");add("assistant","resolved","Thank you. The incident is resolved and the complete activity record is available.");terminal="resolved";confirmation="confirmed"
  conversations.append({"conversation_id":conversation_id,"seed":case["seed"],"tenant_id":policy["tenant_id"],"incident_case_id":case["case_id"],"incident_id":case["incident_id"],"domain":domain,"employee_persona_id":endpoint["primary_user_id"],"endpoint_id":endpoint["id"],"branch":branch,"decisions":{"diagnostic_consent":consent,"remediation_approval":approval,"employee_confirmation":confirmation},"terminal_state":terminal,"turns":turns,"replay":{"generator_version":"1.0.0","master_seed":policy["seed"],"source_case_seed":case["seed"],"branch":branch}})
 payload={"schema_version":"1.0.0","synthetic_only":True,"tenant_id":policy["tenant_id"],"seed":policy["seed"],"conversation_count":len(conversations),"conversations":conversations};payload["dataset_digest"]=digest(payload);return payload
def canonical_bytes()->bytes:return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__":DESTINATION.write_bytes(canonical_bytes());print(DESTINATION)
