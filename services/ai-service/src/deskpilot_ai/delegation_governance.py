from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Literal

MAX_DELEGATION_DEPTH = 2
MAX_FANOUT = 2
MAX_CHILD_TOOL_CALLS = 8
MAX_CHILD_TOKENS = 3000
MAX_CHILD_SECONDS = 120
NON_DELEGABLE_AUTHORITIES = frozenset({"grant_consent","approve_remediation","issue_capability_token","execute_remediation","confirm_employee_experience","close_incident","publish_knowledge"})
DELEGATION_NAMESPACE = uuid.UUID("3d50ade0-f369-5dbb-83ba-5856ef372f60")


class DelegationDenied(ValueError):
    pass


@dataclass(frozen=True)
class ParentAuthority:
    tenant_id: str
    incident_id: str
    thread_id: str
    agent_id: str
    capabilities: frozenset[str]
    authorities: frozenset[str]
    remaining_tool_calls: int
    remaining_tokens: int
    remaining_seconds: int
    depth: int


@dataclass(frozen=True)
class DelegationRequest:
    child_agent_id: str
    task_type: str
    objective: str
    input_schema_version: str
    output_schema_version: str
    evidence_ids: tuple[str,...]
    requested_capabilities: frozenset[str]
    requested_authorities: frozenset[str]
    tool_call_budget: int
    token_budget: int
    timeout_seconds: int
    sibling_count: int


@dataclass(frozen=True)
class DelegationContract:
    delegation_id: str
    tenant_id: str
    incident_id: str
    thread_id: str
    parent_agent_id: str
    child_agent_id: str
    task_type: str
    objective: str
    input_schema_version: str
    output_schema_version: str
    evidence_ids: tuple[str,...]
    capabilities: tuple[str,...]
    tool_call_budget: int
    token_budget: int
    timeout_seconds: int
    depth: int
    status: Literal["authorized"]
    provenance_sha256: str


@dataclass(frozen=True)
class ChildResult:
    delegation_id: str
    child_agent_id: str
    status: Literal["complete","partial","failed","timeout","cancelled"]
    output_schema_version: str
    evidence_ids: tuple[str,...]
    tool_calls_used: int
    tokens_used: int
    elapsed_seconds: int
    attempted_authorities: frozenset[str]
    output_fingerprint: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def authorize(parent: ParentAuthority, request: DelegationRequest) -> DelegationContract:
    if not all((parent.tenant_id,parent.incident_id,parent.thread_id,parent.agent_id,request.child_agent_id,request.task_type,request.objective)): raise DelegationDenied("delegation scope incomplete")
    if parent.depth+1>MAX_DELEGATION_DEPTH or request.sibling_count>=MAX_FANOUT: raise DelegationDenied("delegation depth or fan-out exceeded")
    if not request.requested_capabilities<=parent.capabilities or request.requested_authorities or request.requested_authorities&NON_DELEGABLE_AUTHORITIES: raise DelegationDenied("capability expansion or authority transfer prohibited")
    if not 0<request.tool_call_budget<=min(parent.remaining_tool_calls,MAX_CHILD_TOOL_CALLS) or not 0<request.token_budget<=min(parent.remaining_tokens,MAX_CHILD_TOKENS) or not 0<request.timeout_seconds<=min(parent.remaining_seconds,MAX_CHILD_SECONDS): raise DelegationDenied("child budget exceeds parent or policy")
    if not request.evidence_ids or len(set(request.evidence_ids))!=len(request.evidence_ids): raise DelegationDenied("bounded evidence contract required")
    stable=":".join((parent.tenant_id,parent.incident_id,parent.thread_id,parent.agent_id,request.child_agent_id,request.task_type,str(parent.depth+1)));delegation_id=str(uuid.uuid5(DELEGATION_NAMESPACE,stable))
    payload={"id":delegation_id,"scope":(parent.tenant_id,parent.incident_id,parent.thread_id),"parent":parent.agent_id,"child":request.child_agent_id,"task":request.task_type,"objective":request.objective,"schemas":(request.input_schema_version,request.output_schema_version),"evidence":request.evidence_ids,"capabilities":sorted(request.requested_capabilities),"budgets":(request.tool_call_budget,request.token_budget,request.timeout_seconds),"depth":parent.depth+1}
    return DelegationContract(delegation_id,parent.tenant_id,parent.incident_id,parent.thread_id,parent.agent_id,request.child_agent_id,request.task_type,request.objective,request.input_schema_version,request.output_schema_version,request.evidence_ids,tuple(sorted(request.requested_capabilities)),request.tool_call_budget,request.token_budget,request.timeout_seconds,parent.depth+1,"authorized",_digest(payload))


def validate_result(contract: DelegationContract, result: ChildResult, *, cancelled: bool=False) -> dict[str,object]:
    if result.delegation_id!=contract.delegation_id or result.child_agent_id!=contract.child_agent_id or result.output_schema_version!=contract.output_schema_version: raise DelegationDenied("child result contract mismatch")
    if result.tool_calls_used>contract.tool_call_budget or result.tokens_used>contract.token_budget or result.elapsed_seconds>contract.timeout_seconds: raise DelegationDenied("child exceeded delegated budget")
    if result.attempted_authorities or result.attempted_authorities&NON_DELEGABLE_AUTHORITIES: raise DelegationDenied("child attempted authority")
    if not set(result.evidence_ids)<=set(contract.evidence_ids) or len(result.output_fingerprint)!=64: raise DelegationDenied("child evidence or output provenance invalid")
    if cancelled and result.status!="cancelled": raise DelegationDenied("result arrived after cancellation")
    accepted=result.status in {"complete","partial"} and not cancelled
    return {"delegation_status":"accepted" if accepted else result.status,"delegation_id":contract.delegation_id,"delegation_child_agent_id":contract.child_agent_id,"delegation_result_fingerprint":result.output_fingerprint,"delegation_provenance_sha256":_digest((contract.provenance_sha256,result.output_fingerprint,result.status)),"specialist_status":"complete" if result.status=="complete" else "insufficient_evidence" if result.status=="partial" else "failed"}
