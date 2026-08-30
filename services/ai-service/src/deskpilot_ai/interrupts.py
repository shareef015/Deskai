from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from dataclasses import asdict,dataclass
from typing import Any,Literal,Mapping

INTERRUPT_NAMESPACE=uuid.UUID("68fba252-1a9e-56ac-b5b7-5d5a56349892")
Kind=Literal["diagnostic_consent","remediation_approval","employee_confirmation"]
Decision=Literal["granted","declined","approved","rejected","confirmed","not_fixed"]
DECISIONS={"diagnostic_consent":frozenset({"granted","declined"}),"remediation_approval":frozenset({"approved","rejected"}),"employee_confirmation":frozenset({"confirmed","not_fixed"})}
RISK_ROLES={"read_only":frozenset({"employee"}),"low":frozenset({"employee","service_desk_engineer"}),"medium":frozenset({"remediation_approver","l2_l3_specialist"}),"high":frozenset({"endpoint_administrator","network_administrator","identity_exchange_administrator","security_administrator"})}
MAX_TTL={"diagnostic_consent":30,"remediation_approval":15,"employee_confirmation":60}

class ResumeDenied(PermissionError):pass
class DecisionConflict(RuntimeError):pass

@dataclass(frozen=True,slots=True)
class DecisionPrincipal:
 subject:str;tenant_id:str;roles:frozenset[str];is_ai:bool=False
@dataclass(frozen=True,slots=True)
class InterruptRequest:
 request_id:str;version:str;kind:Kind;tenant_id:str;incident_id:str;thread_id:str;checkpoint_id:str;employee_id:str;device_id:str;purpose:str;capabilities:tuple[str,...];risk_level:str;requester_id:str|None;action_id:str|None;issued_at:str;expires_at:str;status:str="pending";revoked_at:str|None=None
 def payload(self)->dict[str,Any]:return asdict(self)
@dataclass(frozen=True,slots=True)
class DecisionSubmission:
 request_id:str;version:str;decision:Decision;reason:str|None=None

def _utc(value:str)->dt.datetime:
 parsed=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if parsed.tzinfo is None:raise ResumeDenied("timezone-aware decision time required")
 return parsed.astimezone(dt.timezone.utc)
def _canonical(value:Mapping[str,Any])->str:return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def decision_fingerprint(request:InterruptRequest,principal:DecisionPrincipal,submission:DecisionSubmission)->str:return hashlib.sha256(_canonical({"request_id":request.request_id,"version":request.version,"tenant_id":request.tenant_id,"actor_id":principal.subject,"decision":submission.decision,"reason":submission.reason}).encode()).hexdigest()
def new_request(*,kind:Kind,tenant_id:str,incident_id:str,thread_id:str,checkpoint_id:str,employee_id:str,device_id:str,purpose:str,capabilities:tuple[str,...],risk_level:str="read_only",requester_id:str|None=None,action_id:str|None=None,issued_at:dt.datetime,ttl_minutes:int)->InterruptRequest:
 if ttl_minutes<1 or ttl_minutes>MAX_TTL[kind]:raise ValueError("interrupt TTL exceeds policy")
 if issued_at.tzinfo is None:raise ValueError("issued_at must be timezone-aware")
 if kind=="remediation_approval" and (not action_id or risk_level not in RISK_ROLES):raise ValueError("approval interrupt requires typed action and risk")
 stable=f"{kind}:{tenant_id}:{incident_id}:{thread_id}:{checkpoint_id}:{employee_id}:{device_id}:{action_id or ''}"
 return InterruptRequest(str(uuid.uuid5(INTERRUPT_NAMESPACE,stable)),"1.0.0",kind,tenant_id,incident_id,thread_id,checkpoint_id,employee_id,device_id,purpose,capabilities,risk_level,requester_id,action_id,issued_at.astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z"),(issued_at+dt.timedelta(minutes=ttl_minutes)).astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z"))

def validate_resume(*,request:InterruptRequest,principal:DecisionPrincipal,submission:DecisionSubmission,now:dt.datetime,expected_scope:Mapping[str,str],assigned_device_ids:frozenset[str],existing_fingerprint:str|None=None)->dict[str,Any]:
 if principal.is_ai or "ai_service" in principal.roles or "auditor" in principal.roles:raise ResumeDenied("actor cannot make human decision")
 if request.status!="pending" or request.revoked_at is not None:raise ResumeDenied("interrupt is no longer pending")
 if now.tzinfo is None or now.astimezone(dt.timezone.utc)>_utc(request.expires_at):raise ResumeDenied("interrupt expired")
 if submission.request_id!=request.request_id or submission.version!=request.version or submission.decision not in DECISIONS[request.kind]:raise ResumeDenied("decision does not match interrupt")
 scope={"tenant_id":request.tenant_id,"incident_id":request.incident_id,"thread_id":request.thread_id,"checkpoint_id":request.checkpoint_id}
 if any(expected_scope.get(key)!=value for key,value in scope.items()) or principal.tenant_id!=request.tenant_id:raise ResumeDenied("resume scope mismatch")
 if request.kind in {"diagnostic_consent","employee_confirmation"}:
  if principal.subject!=request.employee_id or "employee" not in principal.roles or request.device_id not in assigned_device_ids:raise ResumeDenied("employee decision authority mismatch")
 elif request.kind=="remediation_approval":
  if principal.subject==request.requester_id or not principal.roles.intersection(RISK_ROLES[request.risk_level]):raise ResumeDenied("approval authority or segregation of duties mismatch")
 fingerprint=decision_fingerprint(request,principal,submission)
 if existing_fingerprint is not None and existing_fingerprint!=fingerprint:raise DecisionConflict("interrupt already has a different decision")
 return {"validated_by_server":True,"request_id":request.request_id,"version":request.version,"kind":request.kind,"decision":submission.decision,"actor_id":principal.subject,"tenant_id":request.tenant_id,"incident_id":request.incident_id,"thread_id":request.thread_id,"checkpoint_id":request.checkpoint_id,"decision_fingerprint":fingerprint,"idempotent_replay":existing_fingerprint==fingerprint,"decided_at":now.astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z")}

async def resume_graph(graph:Any,*,config:Mapping[str,Any],validated_envelope:Mapping[str,Any])->Any:
 if validated_envelope.get("validated_by_server") is not True:raise ResumeDenied("unvalidated resume envelope")
 from langgraph.types import Command
 return await graph.ainvoke(Command(resume=dict(validated_envelope)),config=dict(config))
