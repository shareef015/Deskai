from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
Client=Literal["classic_outlook","new_outlook"]
MAX_DIAGNOSTICS=8;MAX_HYPOTHESES=5;MAX_RAG_QUERIES=2;MAX_REMEDIATIONS=3;MIN_ROOT_CAUSE_CONFIDENCE=.75
READ_ONLY_TOOLS=frozenset({"outlook_health","outlook_connectivity","outlook_addins","outlook_profile_metadata"})
CLIENT_PROCESSES={"outlook.exe":"classic_outlook","olk.exe":"new_outlook"};NEW_OUTLOOK_PROHIBITED=frozenset({"enumerate_com_addins","inspect_classic_profiles","scanpst","safe_mode"})
INCIDENT_PLANS={
 "startup":("detect_client","inspect_process","collect_app_events","check_recent_updates","check_disk_space"),
 "crash":("detect_client","inspect_process","collect_app_events","check_build","inspect_addins_if_classic"),
 "connectivity":("detect_client","check_service_health","check_work_offline_if_classic","test_dns","inspect_proxy","inspect_vpn","test_m365_endpoints"),
 "authentication":("detect_client","check_service_health","check_device_time","inspect_auth_events_without_secrets","compare_browser_sign_in"),
 "sync":("detect_client","check_service_health","inspect_sync_state","test_m365_endpoints","inspect_data_file_metadata_if_classic"),
 "search":("detect_client","inspect_search_state","inspect_index_scope_if_classic","check_build"),
 "add_in":("detect_client","inspect_addins_if_classic","collect_app_events","check_build")}
class OutlookSpecialistError(ValueError):pass
@dataclass(frozen=True)
class OutlookContext:tenant_id:str;incident_id:str;device_id:str;consent_status:str;process_name:str|None;windows_version:str;outlook_build:str|None;incident_class:str
@dataclass(frozen=True)
class DiagnosticPlan:client:Client|None;steps:tuple[str,...];tools:tuple[str,...];rag_queries:tuple[dict[str,object],...];outcome:Literal["diagnose","clarify","escalate"];reason:str;provenance_sha256:str
@dataclass(frozen=True)
class Hypothesis:name:str;confidence:float;evidence_ids:tuple[str,...];knowledge_source_ids:tuple[str,...]
@dataclass(frozen=True)
class RemediationProposal:action:str;risk:Literal["low","medium","high"];required_approver:str;pre_state_required:bool;rollback:str|None;verification:tuple[str,...]
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def detect_client(process_name:str|None)->Client|None:return CLIENT_PROCESSES.get((process_name or "").lower())
def plan_diagnostics(context:OutlookContext)->DiagnosticPlan:
 if context.consent_status!="granted":raise OutlookSpecialistError("diagnostic consent required")
 client=detect_client(context.process_name)
 if client is None:return DiagnosticPlan(None,(),(),(),"clarify" if context.process_name is None else "escalate","outlook_client_unknown",_digest(context.__dict__))
 if context.incident_class not in INCIDENT_PLANS:return DiagnosticPlan(client,(),(),(),"escalate","unsupported_outlook_incident_class",_digest(context.__dict__))
 steps=list(INCIDENT_PLANS[context.incident_class])
 if client=="new_outlook":steps=[x for x in steps if not x.endswith("_if_classic")]
 tools=["outlook_health","outlook_connectivity","outlook_profile_metadata"]
 if client=="classic_outlook" and "inspect_addins_if_classic" in steps:tools.append("outlook_addins")
 filters={"tenant_id":context.tenant_id,"product":"outlook","client":client,"outlook_build":context.outlook_build or "unknown","windows_version":context.windows_version,"incident_class":context.incident_class,"permission":"employee_support"}
 queries=({"query":f"{client} {context.incident_class} diagnostics and verification","filters":filters},)
 payload={"client":client,"steps":steps,"tools":sorted(tools),"rag_queries":queries};return DiagnosticPlan(client,tuple(steps[:MAX_DIAGNOSTICS]),tuple(sorted(tools)),queries,"diagnose","version_aware_plan",_digest(payload))
def validate_hypotheses(items:tuple[Hypothesis,...])->Literal["root_cause_ready","insufficient_evidence","contradictory_evidence"]:
 if not items or len(items)>MAX_HYPOTHESES:raise OutlookSpecialistError("invalid hypotheses")
 for item in items:
  if not item.name or isinstance(item.confidence,bool) or not 0<=item.confidence<=1 or not item.evidence_ids or len(set(item.evidence_ids))!=len(item.evidence_ids):raise OutlookSpecialistError("ungrounded hypothesis")
 ordered=sorted(items,key=lambda x:(-x.confidence,x.name))
 if len(ordered)>1 and ordered[0].confidence-ordered[1].confidence<.1 and ordered[1].confidence>=MIN_ROOT_CAUSE_CONFIDENCE:return "contradictory_evidence"
 return "root_cause_ready" if ordered[0].confidence>=MIN_ROOT_CAUSE_CONFIDENCE else "insufficient_evidence"
def validate_remediation(proposal:RemediationProposal)->None:
 if not proposal.action or len(proposal.verification)<2 or "employee_confirms" not in proposal.verification:raise OutlookSpecialistError("verification incomplete")
 if proposal.risk in {"medium","high"} and (not proposal.pre_state_required or not proposal.rollback):raise OutlookSpecialistError("persistent change requires pre-state and rollback")
 if proposal.risk=="high" and proposal.required_approver not in {"identity_administrator","network_administrator","endpoint_administrator","l2_l3_specialist"}:raise OutlookSpecialistError("qualified high-risk approver required")
def specialist_handoff(plan:DiagnosticPlan,hypotheses:tuple[Hypothesis,...],proposals:tuple[RemediationProposal,...])->dict[str,object]:
 if len(proposals)>MAX_REMEDIATIONS:raise OutlookSpecialistError("too many remediation proposals")
 status=validate_hypotheses(hypotheses)
 for proposal in proposals:validate_remediation(proposal)
 phase="evidence_fusion" if status=="root_cause_ready" else "clarification" if status=="insufficient_evidence" else "evidence_fusion"
 return {"phase":phase,"outlook_client":plan.client,"outlook_diagnostic_plan_sha256":plan.provenance_sha256,"outlook_hypothesis_status":status,"hypotheses":tuple(x.name for x in hypotheses),"remediation_proposals":tuple(x.__dict__ for x in proposals)}
