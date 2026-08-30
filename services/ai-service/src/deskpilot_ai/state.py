from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Literal, NotRequired, Required, TypedDict, TypeVar

MAX_MESSAGES=100;MAX_EVIDENCE=200;MAX_ERRORS=50;MAX_RETRY_NODES=64;MAX_RETRY_PER_NODE=3;MAX_GRAPH_STEPS=80;MAX_TOOL_CALLS=30;MAX_RETRIEVAL_ROUNDS=3

class MessageRecord(TypedDict):
 message_id:Required[str];sequence:Required[int];role:Required[Literal["employee","assistant","system","tool"]];content:Required[str];created_at:Required[str];correlation_id:Required[str]
class EvidenceRecord(TypedDict):
 evidence_id:Required[str];tenant_id:Required[str];incident_id:Required[str];source:Required[str];kind:Required[str];observed_at:Required[str];summary:Required[str];content_included:Required[bool];digest:Required[str]
class SafeError(TypedDict):
 error_id:Required[str];sequence:Required[int];category:Required[str];node:Required[str];code:Required[str];safe_message:Required[str];retryable:Required[bool];correlation_id:Required[str]
class ConsentState(TypedDict):
 status:Required[Literal["not_requested","pending","granted","declined","revoked","expired"]];consent_id:NotRequired[str];device_id:NotRequired[str];capabilities:NotRequired[tuple[str,...]];expires_at:NotRequired[str]
class ApprovalState(TypedDict):
 status:Required[Literal["not_required","pending","approved","rejected","expired"]];approval_id:NotRequired[str];action_id:NotRequired[str];risk_level:NotRequired[str];approver_id:NotRequired[str];expires_at:NotRequired[str]
class Budgets(TypedDict):
 graph_steps_remaining:Required[int];tool_calls_remaining:Required[int];retrieval_rounds_remaining:Required[int]

T=TypeVar("T",bound=Mapping[str,Any])
def _canonical(item:Mapping[str,Any])->str:return json.dumps(item,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def _bounded_records(current:Sequence[T]|None,updates:Sequence[T]|None,*,identity:str,order:tuple[str,...],limit:int)->tuple[T,...]:
 merged:dict[str,T]={}
 for item in tuple(current or ())+tuple(updates or ()):
  key=str(item[identity]);existing=merged.get(key)
  if existing is None or _canonical(item)>_canonical(existing):merged[key]=item
 def sort_key(item:T)->tuple[Any,...]:return tuple(item.get(field) for field in order)+(str(item[identity]),)
 return tuple(sorted(merged.values(),key=sort_key)[-limit:])
def merge_messages(current:Sequence[MessageRecord]|None,updates:Sequence[MessageRecord]|None)->tuple[MessageRecord,...]:return _bounded_records(current,updates,identity="message_id",order=("sequence",),limit=MAX_MESSAGES)
def merge_evidence(current:Sequence[EvidenceRecord]|None,updates:Sequence[EvidenceRecord]|None)->tuple[EvidenceRecord,...]:return _bounded_records(current,updates,identity="evidence_id",order=("observed_at",),limit=MAX_EVIDENCE)
def merge_errors(current:Sequence[SafeError]|None,updates:Sequence[SafeError]|None)->tuple[SafeError,...]:return _bounded_records(current,updates,identity="error_id",order=("sequence",),limit=MAX_ERRORS)
def merge_retry_counts(current:Mapping[str,int]|None,updates:Mapping[str,int]|None)->dict[str,int]:
 merged=dict(current or {})
 for node,count in (updates or {}).items():merged[node]=min(MAX_RETRY_PER_NODE,max(merged.get(node,0),count))
 return dict(sorted(merged.items())[:MAX_RETRY_NODES])

class GraphInput(TypedDict):
 tenant_id:Required[str];incident_id:Required[str];thread_id:Required[str];correlation_id:Required[str];employee_id:Required[str];device_id:Required[str];initial_message:Required[str]
class GraphOutput(TypedDict):
 incident_id:Required[str];status:Required[Literal["resolved","escalated","cancelled"]];employee_message:Required[str];evidence_ids:Required[tuple[str,...]];audit_event_ids:Required[tuple[str,...]]
class DeskPilotState(GraphInput,total=False):
 state_version:Required[str]
 phase:Required[str]
 messages:Annotated[tuple[MessageRecord,...],merge_messages]
 evidence:Annotated[tuple[EvidenceRecord,...],merge_evidence]
 errors:Annotated[tuple[SafeError,...],merge_errors]
 retry_counts:Annotated[dict[str,int],merge_retry_counts]
 consent:ConsentState
 approval:ApprovalState
 budgets:Budgets
 hypotheses:tuple[str,...]
 selected_root_cause:str|None
 remediation_plan_id:str|None
 audit_event_ids:tuple[str,...]
 final_status:Literal["resolved","escalated","cancelled"]|None
 pending_interrupt:dict[str,Any]|None
 domain:Literal["outlook","printer","scanner","windows_network","unknown"]
 capability_token_id:str
 route_reason:str
 graph_version:str
 candidate_domains:tuple[Literal["outlook","printer","scanner","windows_network"],...]
 domain_route_outcome:Literal["single","parallel","clarify","escalate"]
 domain_route_reason:str
 domain_route_confidence:float
 domain_route_provenance_sha256:str
 specialist_status:Literal["complete","insufficient_evidence","contradictory_evidence","blocked","failed"]
 specialist_summary:str
 specialist_provenance_sha256:str
 diagnostic_fanout_status:Literal["complete","partial","contradictory","failed"]
 contradiction_keys:tuple[str,...]
 diagnostic_fanout_provenance_sha256:str
 termination_reason:str
 termination_proof:dict[str,Any]
 incident_summary:str
 symptoms:tuple[str,...]
 business_impact:str
 affected_device_id:str|None
 reported_timeline:str|None
 domain_candidates:tuple[dict[str,Any],...]
 uncertain_fields:tuple[str,...]
 clarification_needs:tuple[str,...]
 intake_evidence_references:tuple[str,...]
 intake_source_digest:str
 intake_extraction_version:str
 clarification_round:int
 clarification_questions:tuple[str,...]
 asked_clarification_ids:tuple[str,...]
 clarification_reason:str
 clarification_provenance_sha256:str
 device_resolution_status:Literal["pending_confirmation","ambiguous","not_found","confirmed","declined","escalated"]
 device_candidates:tuple[dict[str,Any],...]
 device_confirmation_token:str|None
 device_resolution_reason:str
 device_resolution_provenance_sha256:str
 outlook_client:Literal["classic_outlook","new_outlook"]|None
 outlook_diagnostic_plan_sha256:str
 outlook_hypothesis_status:Literal["root_cause_ready","insufficient_evidence","contradictory_evidence"]
 remediation_proposals:tuple[dict[str,Any],...]
 print_scan_domain:Literal["printer","scanner"]
 print_scan_topology:Literal["local_usb","direct_network","print_server","multifunction"]|None
 print_scan_plan_sha256:str
 print_scan_hypothesis_status:Literal["root_cause_ready","insufficient_evidence","contradictory_evidence"]
 windows_network_domain:Literal["windows","network"]
 windows_network_plan_sha256:str
 windows_network_hypothesis_status:Literal["root_cause_ready","insufficient_evidence","contradictory_evidence"]
 evidence_fusion_status:Literal["root_cause_ready","insufficient_evidence","contradictory_evidence","escalate"]
 ranked_hypotheses:tuple[dict[str,Any],...]
 evidence_fusion_provenance_sha256:str
 remediation_plan_status:Literal["approval_required","escalate"]
 remediation_maximum_risk:Literal["low","medium","high"]
 required_approvers:tuple[str,...]
 remediation_plan_provenance_sha256:str
 planned_actions:tuple[str,...]
 remediation_critic_status:Literal["pass","revise","escalate"]
 remediation_critic_findings:tuple[dict[str,Any],...]
 reviewed_plan_id:str
 remediation_critic_provenance_sha256:str
 approval_packet_id:str
 approval_actor_id:str
 approval_decision_fingerprint:str
 execution_token_id:str
 execution_status:Literal["succeeded","failed","partial","timeout"]
 execution_result_fingerprint:str
 execution_recovery_route:Literal["verify_change","rollback","human_recovery"]
 verification_status:Literal["awaiting_confirmation","failed","regression","inconclusive","verified","employee_reports_not_fixed"]
 verification_recovery_route:Literal["employee_confirmation","rollback","escalate","collect_more_evidence"]
 verification_provenance_sha256:str
 regression_check_ids:tuple[str,...]
 employee_confirmation_actor_id:str
 closure_status:Literal["closed","reopened","escalated"]
 resolution_summary:str
 closure_provenance_sha256:str
 knowledge_candidate_id:str|None
 handoff_status:Literal["pending_acknowledgement","acknowledged","resolved_by_human","returned_for_information","transferred"]
 handoff_actor_id:str
 handoff_owner_team:str
 handoff_resume_route:Literal["await_human_action","verify_human_change","collect_requested_information","transfer_owner"]
 handoff_action_fingerprint:str
 agent_trace_id:str
 agent_trace_head_sha256:str
 agent_trace_event_count:int
 total_model_tokens:int
 total_model_cost_microusd:int
 total_agent_latency_ms:int
 agent_health_status:Literal["healthy","degraded","critical"]
 agent_traffic_action:Literal["continue","increase_review","safe_fallback"]
 agent_execution_action:Literal["continue","require_extra_review","freeze_automated_execution"]
 agent_monitoring_provenance_sha256:str
 auth_session_id:str
 authenticated_subject_id:str
 authenticated_roles:tuple[str,...]
 session_mode:Literal["live","synthetic"]
 session_expires_at:int
 active_persona_id:str|None
 auth_provenance_sha256:str
 navigation_manifest_sha256:str
 active_navigation_key:str
 application_mode:Literal["live","synthetic"]
 tenant_display_label:str
 pending_action_kind:Literal["diagnostic_consent","remediation_decision","handoff_note","employee_confirmation"]|None
 action_surface_status:Literal["idle","editing","confirming","submitting","succeeded","failed","cancelled"]
 action_request_id:str|None
 action_payload_sha256:str
 advanced_investigation_status:Literal["unavailable","ready","bounded","blocked"]
 investigation_node_ids:tuple[str,...]
 investigation_edge_count:int
 investigation_view_provenance_sha256:str
 frontend_schema_version:str
 frontend_view_model_sha256:str
 accessibility_contract_status:Literal["passed","failed"]
 workspace_theme_id:str
 remote_support_stage:Literal["intake","clarification","permission","ui_diagnostics","change_approval","ui_repair","verification","resolved","declined","revoked"]
 remote_access_request_id:str|None
 remote_session_id:str|None
 remote_session_expires_at:int|None
 remote_session_capabilities:tuple[str,...]
 selected_model_id:str|None
 selected_model_provider_id:str|None
 model_route_outcome:Literal["selected","fallback_selected","escalate"]
 model_route_reason:str
 model_route_provenance_sha256:str
 cache_outcome:Literal["hit","miss","bypass","stale","revalidation_failed"]
 cache_key_sha256:str
 cache_cost_saved_microusd:int
 compressed_history_provenance_sha256:str
 context_original_tokens:int
 context_compressed_tokens:int
 prompt_firewall_outcome:Literal["allow","isolate","block"]
 prompt_firewall_detections:tuple[str,...]
 prompt_firewall_provenance_sha256:str
 recalled_memory_ids:tuple[str,...]
 memory_scope_provenance_sha256:str
 planning_status:Literal["critic_review","approved_for_orchestration","escalate"]
 planning_plan_sha256:str
 planning_ordered_step_ids:tuple[str,...]
 planning_maximum_risk:Literal["read_only","low","medium","high"]
 delegation_status:Literal["authorized","accepted","partial","failed","timeout","cancelled"]
 delegation_id:str
 delegation_child_agent_id:str
 delegation_result_fingerprint:str
 delegation_provenance_sha256:str
 tool_authorization_outcome:Literal["allow","deny"]
 tool_authorization_reason:str
 tool_authorization_decision_sha256:str
 mcp_dispatch_status:Literal["validated","denied","quarantined"]
 mcp_envelope_id:str
 mcp_result_sha256:str
 mcp_evidence_lineage_sha256:str
 integration_readiness_status:Literal["ready","blocked"]
 integration_readiness_report_sha256:str
 runtime_last_event_cursor:int
 runtime_last_command_id:str
 pending_human_interrupt_id:str|None
 human_interrupt_status:Literal["pending","approved","rejected","declined","confirmed","not_fixed","expired","revoked"]|None
 human_decision_fingerprint:str|None
 conversation_last_cursor:int
 conversation_stopped:bool
 conversation_active_message_id:str|None
 evidence_explorer_filter:str|None
 selected_evidence_ids:tuple[str,...]
 evidence_export_sha256:str|None
 remediation_review_status:Literal["pending","approved","rejected","expired","superseded"]|None
 remediation_review_decision_sha256:str|None
 execution_run_id:str|None
 execution_last_action_id:str|None
 rollback_verification_status:Literal["not_required","pending","verified","failed"]|None
 human_handoff_id:str|None
 human_custody_status:Literal["queued","acknowledged","verification_required","returned_for_verification"]|None
 human_change_sha256:str|None
 closure_record_sha256:str|None
 closure_sla_outcome:Literal["met","breached"]|None
 reopen_reason:str|None
 knowledge_review_status:Literal["review","published","retired"]|None
 knowledge_version_id:str|None
 knowledge_index_refresh_sha256:str|None
 operations_queue_cursor:int
 operations_stalled:bool
 operations_alerts:tuple[str,...]
 observability_trace_cursor:int
 observability_SLO_status:Literal["healthy","warning","breach"]|None
 observability_drift_alert:bool
 evaluation_run_sha256:str|None
 evaluation_gate_status:Literal["blocked","review","approved"]|None
 evaluation_blocker_count:int
 AI_release_bundle_id:str|None
 AI_release_canary_percent:int
 AI_release_frozen:bool

def new_state(input_state:GraphInput)->DeskPilotState:
 return {**input_state,"state_version":"1.0.0","phase":"greeting","messages":(),"evidence":(),"errors":(),"retry_counts":{},"consent":{"status":"not_requested"},"approval":{"status":"not_required"},"budgets":{"graph_steps_remaining":MAX_GRAPH_STEPS,"tool_calls_remaining":MAX_TOOL_CALLS,"retrieval_rounds_remaining":MAX_RETRIEVAL_ROUNDS},"hypotheses":(),"selected_root_cause":None,"remediation_plan_id":None,"audit_event_ids":(),"final_status":None,"pending_interrupt":None}

def validate_state(state:Mapping[str,Any])->list[str]:
 errors=[]
 for field in ("tenant_id","incident_id","thread_id","correlation_id","employee_id","device_id","state_version","phase"):
  if not isinstance(state.get(field),str) or not state[field]:errors.append(f"{field} is required")
 if state.get("state_version")!="1.0.0":errors.append("unsupported state version")
 phases={"greeting","intake","clarification","classification","consent","diagnosis","evidence_fusion","remediation_planning","approval","execution","verification","confirmation","resolved","escalated","cancelled"}
 if state.get("phase") not in phases:errors.append("invalid graph phase")
 messages=tuple(state.get("messages",()));evidence=tuple(state.get("evidence",()));safe_errors=tuple(state.get("errors",()))
 if len(messages)>MAX_MESSAGES or len(evidence)>MAX_EVIDENCE or len(safe_errors)>MAX_ERRORS:errors.append("bounded history exceeded")
 for records,key in ((messages,"message_id"),(evidence,"evidence_id"),(safe_errors,"error_id")):
  ids=[item.get(key) for item in records]
  if len(ids)!=len(set(ids)):errors.append(f"duplicate {key}")
 if any(item.get("tenant_id")!=state.get("tenant_id") or item.get("incident_id")!=state.get("incident_id") for item in evidence):errors.append("cross-scope evidence")
 if any(item.get("content_included") is not False for item in evidence):errors.append("unbounded evidence content")
 retries=state.get("retry_counts",{})
 if len(retries)>MAX_RETRY_NODES or any(not isinstance(v,int) or v<0 or v>MAX_RETRY_PER_NODE for v in retries.values()):errors.append("retry budget exceeded")
 budgets=state.get("budgets",{})
 for key,maximum in (("graph_steps_remaining",MAX_GRAPH_STEPS),("tool_calls_remaining",MAX_TOOL_CALLS),("retrieval_rounds_remaining",MAX_RETRIEVAL_ROUNDS)):
  value=budgets.get(key)
  if not isinstance(value,int) or not 0<=value<=maximum:errors.append(f"invalid {key}")
 if state.get("phase")=="execution" and state.get("approval",{}).get("status") not in {"approved","not_required"}:errors.append("execution lacks approval")
 if state.get("phase") in {"resolved","escalated","cancelled"} and state.get("final_status")!=state.get("phase"):errors.append("terminal phase/status mismatch")
 return errors
