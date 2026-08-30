from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from typing import Literal,Mapping,Any
MAX_STEPS=80;MAX_REASONING_TURNS=12;MAX_PHASE_VISITS=3;MAX_IDENTICAL_STATE_VISITS=2;MAX_NO_PROGRESS=2
TERMINALS=frozenset({"resolved","escalated","cancelled"})
TRANSITIONS={
 "greeting":{"intake","cancelled"},"intake":{"clarification","classification","cancelled"},"clarification":{"classification","consent","diagnosis","escalated","cancelled"},"classification":{"clarification","consent","escalated"},"consent":{"diagnosis","cancelled","escalated"},"diagnosis":{"evidence_fusion","clarification","escalated"},"evidence_fusion":{"remediation_planning","clarification","escalated"},"remediation_planning":{"approval","execution","escalated"},"approval":{"execution","escalated","cancelled"},"execution":{"verification","escalated"},"verification":{"confirmation","remediation_planning","escalated"},"confirmation":{"resolved","escalated"}}
@dataclass
class TerminationTracker:
 steps_used:int=0;reasoning_turns_used:int=0;no_progress_transitions:int=0;phase_visits:dict[str,int]=field(default_factory=dict);fingerprint_visits:dict[str,int]=field(default_factory=dict);path:list[str]=field(default_factory=list);last_evidence_count:int=0
@dataclass(frozen=True)
class TransitionDecision:
 next_phase:str;reason:str;must_terminate:bool;state_fingerprint:str
@dataclass(frozen=True)
class TerminationProof:
 terminal_state:Literal["resolved","escalated","cancelled"];reason:str;steps_used:int;reasoning_turns_used:int;last_state_fingerprint:str;path_digest:str
def state_fingerprint(state:Mapping[str,Any])->str:
 payload={"phase":state.get("phase"),"evidence_ids":sorted(str(x.get("evidence_id")) for x in state.get("evidence",())),"selected_root_cause":state.get("selected_root_cause"),"remediation_plan_id":state.get("remediation_plan_id"),"consent_status":state.get("consent",{}).get("status"),"approval_status":state.get("approval",{}).get("status")}
 return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def guard_transition(state:Mapping[str,Any],proposed_phase:str,tracker:TerminationTracker,*,reasoning_turn:bool=False,evidence_sufficient:bool=True)->TransitionDecision:
 current=str(state.get("phase"));fingerprint=state_fingerprint(state)
 if current in TERMINALS:return TransitionDecision(current,"terminal_state_immutable",True,fingerprint)
 tracker.steps_used+=1;tracker.reasoning_turns_used+=int(reasoning_turn);tracker.phase_visits[current]=tracker.phase_visits.get(current,0)+1;tracker.fingerprint_visits[fingerprint]=tracker.fingerprint_visits.get(fingerprint,0)+1;tracker.path.append(current)
 evidence_count=len(tuple(state.get("evidence",())));tracker.no_progress_transitions=tracker.no_progress_transitions+1 if evidence_count<=tracker.last_evidence_count and proposed_phase==current else 0;tracker.last_evidence_count=max(tracker.last_evidence_count,evidence_count)
 if tracker.steps_used>MAX_STEPS:return TransitionDecision("escalated","graph_step_budget_exhausted",True,fingerprint)
 if tracker.reasoning_turns_used>MAX_REASONING_TURNS:return TransitionDecision("escalated","reasoning_budget_exhausted",True,fingerprint)
 if tracker.phase_visits[current]>MAX_PHASE_VISITS:return TransitionDecision("escalated","phase_visit_limit_exceeded",True,fingerprint)
 if tracker.fingerprint_visits[fingerprint]>MAX_IDENTICAL_STATE_VISITS:return TransitionDecision("escalated","state_cycle_detected",True,fingerprint)
 if tracker.no_progress_transitions>MAX_NO_PROGRESS:return TransitionDecision("escalated","no_progress_detected",True,fingerprint)
 if proposed_phase not in TRANSITIONS.get(current,set()):return TransitionDecision("escalated","invalid_transition",True,fingerprint)
 if proposed_phase in {"remediation_planning","approval","execution","verification","confirmation","resolved"} and not evidence_sufficient:return TransitionDecision("escalated","insufficient_evidence_abstention",True,fingerprint)
 return TransitionDecision(proposed_phase,"allowed_transition",proposed_phase in TERMINALS,fingerprint)
def make_termination_proof(decision:TransitionDecision,tracker:TerminationTracker)->TerminationProof:
 if decision.next_phase not in TERMINALS or not decision.must_terminate:raise ValueError("terminal decision required")
 path=tracker.path+[decision.next_phase];digest=hashlib.sha256(json.dumps(path,separators=(",",":")).encode()).hexdigest()
 return TerminationProof(decision.next_phase,decision.reason,tracker.steps_used,tracker.reasoning_turns_used,decision.state_fingerprint,digest)
def terminal_state_update(proof:TerminationProof)->dict[str,Any]:return {"phase":proof.terminal_state,"final_status":proof.terminal_state,"pending_interrupt":None,"termination_reason":proof.reason,"termination_proof":proof.__dict__}
