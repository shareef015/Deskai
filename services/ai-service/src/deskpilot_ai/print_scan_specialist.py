from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
Domain=Literal["printer","scanner"];Topology=Literal["local_usb","direct_network","print_server","multifunction"]
MAX_DIAGNOSTICS=10;MAX_HYPOTHESES=5;MAX_RAG_QUERIES=2;MAX_REMEDIATIONS=3;MIN_ROOT_CAUSE_CONFIDENCE=.75
TOOLS={"printer":frozenset({"printer_inventory","print_queue","spooler_status","printer_port","printer_reachability"}),"scanner":frozenset({"scanner_inventory","wia_status","twain_metadata","scanner_reachability"})}
TOPOLOGIES=frozenset({"local_usb","direct_network","print_server","multifunction"})
class PrintScanError(ValueError):pass
@dataclass(frozen=True)
class PrintScanContext:tenant_id:str;incident_id:str;device_id:str;consent_status:str;domain:Domain;topology:Topology|None;windows_version:str;device_model:str|None;driver_or_protocol_version:str|None;protected_print_mode:bool
@dataclass(frozen=True)
class DiagnosticPlan:domain:Domain;topology:Topology|None;steps:tuple[str,...];tools:tuple[str,...];rag_queries:tuple[dict[str,object],...];outcome:Literal["diagnose","clarify","escalate"];reason:str;provenance_sha256:str
@dataclass(frozen=True)
class Hypothesis:name:str;confidence:float;evidence_ids:tuple[str,...]
@dataclass(frozen=True)
class RemediationProposal:action:str;risk:Literal["low","medium","high"];required_approver:str;pre_state_required:bool;rollback:str|None;verification:tuple[str,...]
def _digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def plan_diagnostics(context:PrintScanContext)->DiagnosticPlan:
 if context.consent_status!="granted":raise PrintScanError("diagnostic consent required")
 if context.domain not in TOOLS:raise PrintScanError("unsupported print/scan domain")
 if context.topology is None:return DiagnosticPlan(context.domain,None,(),(),(),"clarify","topology_required",_digest(context.__dict__))
 if context.topology not in TOPOLOGIES:return DiagnosticPlan(context.domain,context.topology,(),(),(),"escalate","unsupported_topology",_digest(context.__dict__))
 if context.domain=="printer":
  steps=["detect_topology","inspect_printer_inventory","inspect_queue","inspect_spooler"]
  if context.topology in {"direct_network","print_server","multifunction"}:steps.extend(("inspect_port","test_reachability"))
  if context.topology=="print_server":steps.append("inspect_print_server_reference")
  steps.append("inspect_protected_print_mode")
 else:
  steps=["detect_topology","inspect_scanner_inventory","inspect_wia","inspect_twain_metadata"]
  if context.topology in {"direct_network","print_server","multifunction"}:steps.append("test_reachability")
 filters={"tenant_id":context.tenant_id,"domain":context.domain,"topology":context.topology,"windows_version":context.windows_version,"device_model":context.device_model or "unknown","driver_or_protocol_version":context.driver_or_protocol_version or "unknown","permission":"employee_support"}
 query=({"query":f"Windows {context.domain} {context.topology} diagnostics and verification","filters":filters},);payload={"steps":steps,"tools":sorted(TOOLS[context.domain]),"query":query};return DiagnosticPlan(context.domain,context.topology,tuple(steps[:MAX_DIAGNOSTICS]),tuple(sorted(TOOLS[context.domain])),query,"diagnose","topology_aware_plan",_digest(payload))
def validate_hypotheses(items:tuple[Hypothesis,...])->str:
 if not items or len(items)>MAX_HYPOTHESES:raise PrintScanError("invalid hypotheses")
 for x in items:
  if not x.name or isinstance(x.confidence,bool) or not 0<=x.confidence<=1 or not x.evidence_ids:raise PrintScanError("ungrounded hypothesis")
 ordered=sorted(items,key=lambda x:(-x.confidence,x.name))
 if len(ordered)>1 and ordered[1].confidence>=MIN_ROOT_CAUSE_CONFIDENCE and ordered[0].confidence-ordered[1].confidence<.1:return "contradictory_evidence"
 return "root_cause_ready" if ordered[0].confidence>=MIN_ROOT_CAUSE_CONFIDENCE else "insufficient_evidence"
def validate_remediation(domain:Domain,proposal:RemediationProposal,*,protected_print_mode:bool)->None:
 if proposal.action=="disable_protected_print_mode":raise PrintScanError("security policy bypass prohibited")
 required=("test_print_submitted","physical_output_confirmed","employee_confirms") if domain=="printer" else ("synthetic_test_scan","artifact_accessible","employee_confirms")
 if not set(required)<=set(proposal.verification):raise PrintScanError("physical output verification incomplete")
 if proposal.risk in {"medium","high"} and (not proposal.pre_state_required or not proposal.rollback):raise PrintScanError("persistent change requires pre-state and rollback")
 if protected_print_mode and "third_party_driver" in proposal.action:raise PrintScanError("protected print compatibility escalation required")
def specialist_handoff(plan:DiagnosticPlan,hypotheses:tuple[Hypothesis,...],proposals:tuple[RemediationProposal,...],*,protected_print_mode:bool)->dict[str,object]:
 if len(proposals)>MAX_REMEDIATIONS:raise PrintScanError("too many proposals")
 status=validate_hypotheses(hypotheses)
 for proposal in proposals:validate_remediation(plan.domain,proposal,protected_print_mode=protected_print_mode)
 return {"phase":"clarification" if status=="insufficient_evidence" else "evidence_fusion","print_scan_domain":plan.domain,"print_scan_topology":plan.topology,"print_scan_plan_sha256":plan.provenance_sha256,"print_scan_hypothesis_status":status,"hypotheses":tuple(x.name for x in hypotheses),"remediation_proposals":tuple(x.__dict__ for x in proposals)}
