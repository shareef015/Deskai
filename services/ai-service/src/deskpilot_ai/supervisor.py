from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any,Literal
from .state import DeskPilotState,validate_state
GRAPH_VERSION="1.0.0";TERMINAL_PHASES=frozenset({"resolved","escalated","cancelled"});SUPPORTED_DOMAINS=frozenset({"outlook","printer","scanner","windows_network"})
class SupervisorInvariantError(RuntimeError):pass
@dataclass(frozen=True)
class RouteDecision:next_node:str;reason:str
def _decision(node:str,reason:str)->RouteDecision:return RouteDecision(node,reason)
def route_supervisor(state:Mapping[str,Any])->RouteDecision:
 errors=validate_state(state)
 if errors:raise SupervisorInvariantError("; ".join(errors))
 phase=str(state["phase"])
 if phase in TERMINAL_PHASES:return _decision("__end__",f"terminal:{phase}")
 if state["budgets"]["graph_steps_remaining"]<=0:return _decision("escalate","graph_step_budget_exhausted")
 if phase=="greeting":return _decision("greet","new_support_conversation")
 if phase=="intake":return _decision("intake","capture_employee_problem")
 if phase=="clarification":return _decision("clarify","required_context_missing")
 if phase=="classification":
  supported=state.get("domain","unknown") in SUPPORTED_DOMAINS
  return _decision("request_consent" if supported else "escalate","supported_domain" if supported else "unsupported_or_unknown_domain")
 if phase=="consent":
  status=state.get("consent",{}).get("status")
  if status=="granted":return _decision("diagnose","diagnostic_consent_valid")
  if status in {"declined","revoked","expired"}:return _decision("cancel",f"diagnostic_consent_{status}")
  return _decision("diagnostic_consent_interrupt","human_consent_required")
 if phase=="diagnosis":
  if state.get("consent",{}).get("status")!="granted":return _decision("escalate","diagnostics_without_valid_consent_blocked")
  return _decision("diagnose","consented_read_only_diagnostics")
 if phase=="evidence_fusion":return _decision("fuse_evidence","diagnostic_evidence_available")
 if phase=="remediation_planning":return _decision("plan_remediation","root_cause_selected")
 if phase=="approval":
  status=state.get("approval",{}).get("status")
  if status in {"approved","not_required"}:return _decision("execute","policy_authorization_satisfied")
  if status in {"rejected","expired"}:return _decision("escalate",f"remediation_approval_{status}")
  return _decision("remediation_approval_interrupt","human_approval_required")
 if phase=="execution":
  if state.get("approval",{}).get("status") not in {"approved","not_required"}:return _decision("escalate","execution_without_authorization_blocked")
  if not state.get("capability_token_id"):return _decision("escalate","capability_token_missing")
  return _decision("execute","bounded_capability_authorized")
 if phase=="verification":return _decision("verify","technical_verification_required")
 if phase=="confirmation":return _decision("employee_confirmation_interrupt","employee_confirmation_required")
 return _decision("escalate","unmapped_phase")
def apply_route_provenance(state:Mapping[str,Any],decision:RouteDecision)->dict[str,Any]:
 return {"budgets":{**state["budgets"],"graph_steps_remaining":max(0,int(state["budgets"]["graph_steps_remaining"])-1)},"route_reason":decision.reason,"graph_version":GRAPH_VERSION}
def terminal_update(status:Literal["resolved","escalated","cancelled"])->dict[str,Any]:return {"phase":status,"final_status":status,"pending_interrupt":None}
def build_supervisor_graph(nodes:Mapping[str,Any],*,checkpointer:Any)->Any:
 from langgraph.graph import END,START,StateGraph
 required={"greet","intake","clarify","request_consent","diagnostic_consent_interrupt","diagnose","fuse_evidence","plan_remediation","remediation_approval_interrupt","execute","verify","employee_confirmation_interrupt","escalate","cancel"};missing=required-set(nodes)
 if missing:raise ValueError(f"missing supervisor nodes: {','.join(sorted(missing))}")
 graph=StateGraph(DeskPilotState)
 for name in sorted(required):graph.add_node(name,nodes[name])
 graph.add_edge(START,"greet");graph.add_edge("greet","intake");graph.add_conditional_edges("intake",lambda s:route_supervisor(s).next_node)
 for source in required-{"greet","intake","escalate","cancel"}:graph.add_conditional_edges(source,lambda s:route_supervisor(s).next_node)
 graph.add_edge("escalate",END);graph.add_edge("cancel",END)
 return graph.compile(checkpointer=checkpointer)
