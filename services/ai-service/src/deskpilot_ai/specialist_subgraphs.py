from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Any,Literal,Mapping
from .state import EvidenceRecord
Domain=Literal["outlook","printer","scanner","windows_network"]
Completion=Literal["complete","insufficient_evidence","contradictory_evidence","blocked","failed"]
MAX_STEPS=12;MAX_TOOL_CALLS=8;MAX_RETRIEVAL_ROUNDS=2;MAX_EVIDENCE=32
TOOLS:dict[Domain,frozenset[str]]={
 "outlook":frozenset({"outlook_health","outlook_connectivity","outlook_addins","outlook_profile_metadata"}),
 "printer":frozenset({"printer_inventory","print_queue","spooler_status","printer_port","printer_reachability"}),
 "scanner":frozenset({"scanner_inventory","wia_status","twain_metadata","scanner_reachability"}),
 "windows_network":frozenset({"adapter_status","ip_configuration","dns_resolution","proxy_status","vpn_status","service_status","event_summary"})}
class SpecialistContractError(ValueError):pass
@dataclass(frozen=True)
class SpecialistInput:
 tenant_id:str;incident_id:str;thread_id:str;correlation_id:str;device_id:str;domain:Domain;symptom_summary:str;consent_id:str;evidence_ids:tuple[str,...]=()
@dataclass(frozen=True)
class SpecialistOutput:
 domain:Domain;status:Completion;evidence:tuple[EvidenceRecord,...];hypotheses:tuple[str,...];questions:tuple[str,...];safe_summary:str;provenance_sha256:str
def validate_input(value:SpecialistInput)->None:
 for field in ("tenant_id","incident_id","thread_id","correlation_id","device_id","symptom_summary","consent_id"):
  if not getattr(value,field):raise SpecialistContractError(f"{field} required")
 if value.domain not in TOOLS:raise SpecialistContractError("unsupported specialist domain")
 if len(value.evidence_ids)>MAX_EVIDENCE or len(set(value.evidence_ids))!=len(value.evidence_ids):raise SpecialistContractError("invalid evidence references")
def new_working_state(value:SpecialistInput)->dict[str,Any]:
 validate_input(value)
 return {"contract_version":"1.0.0","scope":{"tenant_id":value.tenant_id,"incident_id":value.incident_id,"thread_id":value.thread_id,"correlation_id":value.correlation_id,"device_id":value.device_id},"domain":value.domain,"symptom_summary":value.symptom_summary,"consent_id":value.consent_id,"evidence_ids":tuple(value.evidence_ids),"steps_remaining":MAX_STEPS,"tool_calls_remaining":MAX_TOOL_CALLS,"retrieval_rounds_remaining":MAX_RETRIEVAL_ROUNDS,"observations":(),"hypotheses":(),"questions":()}
def authorize_tool(domain:Domain,tool_name:str)->bool:return domain in TOOLS and tool_name in TOOLS[domain]
def validate_output(value:SpecialistOutput,source:SpecialistInput)->None:
 if value.domain!=source.domain:raise SpecialistContractError("domain changed across subgraph")
 if len(value.evidence)>MAX_EVIDENCE:raise SpecialistContractError("evidence limit exceeded")
 for item in value.evidence:
  if item.get("tenant_id")!=source.tenant_id or item.get("incident_id")!=source.incident_id:raise SpecialistContractError("cross-scope evidence")
  if item.get("content_included") is not False:raise SpecialistContractError("raw evidence content prohibited")
 if value.status=="complete" and not value.evidence:raise SpecialistContractError("complete output requires evidence")
def finalize_output(source:SpecialistInput,*,status:Completion,evidence:tuple[EvidenceRecord,...],hypotheses:tuple[str,...]=(),questions:tuple[str,...]=(),safe_summary:str)->SpecialistOutput:
 payload={"domain":source.domain,"status":status,"evidence_ids":[x["evidence_id"] for x in evidence],"hypotheses":hypotheses,"questions":questions,"summary":safe_summary}
 output=SpecialistOutput(source.domain,status,evidence,hypotheses,questions,safe_summary,hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest());validate_output(output,source);return output
def supervisor_handoff(output:SpecialistOutput)->dict[str,Any]:
 if output.status=="complete":phase="evidence_fusion"
 elif output.status in {"insufficient_evidence","contradictory_evidence"}:phase="clarification"
 else:phase="escalated"
 return {"phase":phase,"final_status":"escalated" if phase=="escalated" else None,"evidence":output.evidence,"hypotheses":output.hypotheses,"specialist_status":output.status,"specialist_summary":output.safe_summary,"specialist_provenance_sha256":output.provenance_sha256}
def build_specialist_subgraph(*,collect_node:Any,analyze_node:Any,finalize_node:Any,checkpointer:Any=None)->Any:
 from langgraph.graph import END,START,StateGraph
 graph=StateGraph(dict);graph.add_node("collect",collect_node);graph.add_node("analyze",analyze_node);graph.add_node("finalize",finalize_node);graph.add_edge(START,"collect");graph.add_edge("collect","analyze");graph.add_edge("analyze","finalize");graph.add_edge("finalize",END);return graph.compile(checkpointer=checkpointer)
