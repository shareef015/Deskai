from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

INTERRUPT_ROLES={"diagnostic_consent":frozenset({"employee"}),"remediation_approval":frozenset({"service_desk_engineer","approver"}),"employee_confirmation":frozenset({"employee"})}
TERMINAL=frozenset({"approved","rejected","declined","confirmed","not_fixed","expired","revoked"})
SAFE_PACKET_FIELDS=frozenset({"title","summary","risk_level","evidence_ids","action_ids","plan_diff","expires_at","device_label","rollback_available"})

class InterruptDenied(ValueError):pass

@dataclass(frozen=True)
class Actor:
 subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool

@dataclass(frozen=True)
class InterruptRequest:
 interrupt_id:str;tenant_id:str;incident_id:str;thread_id:str;checkpoint_id:str
 kind:Literal["diagnostic_consent","remediation_approval","employee_confirmation"]
 requester_id:str;employee_id:str;created_at:str;expires_at:str;review_packet:dict[str,object]

@dataclass(frozen=True)
class Decision:
 decision_id:str;interrupt_id:str;tenant_id:str;actor_id:str
 outcome:Literal["approved","rejected","declined","confirmed","not_fixed","revoked"]
 reason_code:str;expected_checkpoint_id:str;decided_at:str

@dataclass
class InterruptRecord:
 request:InterruptRequest;status:str="pending";decision:Decision|None=None;decision_fingerprint:str|None=None;version:int=1;events:list[dict[str,object]]=field(default_factory=list)

def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
def _time(value:str)->datetime:
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
 except ValueError as exc:raise InterruptDenied("invalid timestamp") from exc

class InterruptInbox:
 def __init__(self)->None:self.records:dict[str,InterruptRecord]={};self.decisions:dict[str,str]={};self.cursor=0
 def create(self,actor:Actor,request:InterruptRequest)->InterruptRecord:
  self._scope(actor,request.tenant_id)
  if actor.subject!=request.requester_id or not actor.roles.intersection({"service_desk_engineer","operator","system"}):raise InterruptDenied("authorized requester required")
  if request.interrupt_id in self.records:raise InterruptDenied("interrupt already exists")
  if not set(request.review_packet)<=SAFE_PACKET_FIELDS:raise InterruptDenied("unsafe review packet field")
  if _time(request.expires_at)<=_time(request.created_at):raise InterruptDenied("expiry must follow creation")
  record=InterruptRecord(request);self.records[request.interrupt_id]=record;self._event(record,"interrupt_created",actor.subject);return record
 def list_pending(self,actor:Actor,*,kind:str|None=None)->tuple[InterruptRecord,...]:
  self._scope(actor,actor.tenant_id);rows=[]
  for record in self.records.values():
   request=record.request
   if request.tenant_id!=actor.tenant_id or record.status!="pending" or (kind and request.kind!=kind):continue
   if not actor.roles.intersection(INTERRUPT_ROLES[request.kind]):continue
   if request.kind in {"diagnostic_consent","employee_confirmation"} and actor.subject!=request.employee_id:continue
   rows.append(record)
  return tuple(sorted(rows,key=lambda item:(item.request.expires_at,item.request.interrupt_id)))
 def decide(self,actor:Actor,decision:Decision)->dict[str,object]:
  self._scope(actor,decision.tenant_id);record=self.records.get(decision.interrupt_id)
  if not record or record.request.tenant_id!=decision.tenant_id:raise InterruptDenied("interrupt not found")
  fingerprint=_digest(decision.__dict__)
  if decision.decision_id in self.decisions:
   if self.decisions[decision.decision_id]!=fingerprint:raise InterruptDenied("idempotency conflict")
   return self._view(record,True)
  if record.status in TERMINAL:raise InterruptDenied("interrupt already terminal")
  request=record.request
  if decision.actor_id!=actor.subject:raise InterruptDenied("actor binding mismatch")
  if decision.expected_checkpoint_id!=request.checkpoint_id:raise InterruptDenied("checkpoint concurrency mismatch")
  if not actor.roles.intersection(INTERRUPT_ROLES[request.kind]):raise InterruptDenied("decision authority denied")
  if request.kind in {"diagnostic_consent","employee_confirmation"} and actor.subject!=request.employee_id:raise InterruptDenied("employee binding mismatch")
  if request.kind=="remediation_approval" and actor.subject==request.requester_id:raise InterruptDenied("self approval denied")
  decided=_time(decision.decided_at)
  if decided>=_time(request.expires_at):record.status="expired";self._event(record,"interrupt_expired",actor.subject);raise InterruptDenied("interrupt expired")
  allowed={"diagnostic_consent":{"approved","declined","revoked"},"remediation_approval":{"approved","rejected","revoked"},"employee_confirmation":{"confirmed","not_fixed"}}
  if decision.outcome not in allowed[request.kind]:raise InterruptDenied("outcome not valid for interrupt")
  record.status=decision.outcome;record.decision=decision;record.decision_fingerprint=fingerprint;record.version+=1;self.decisions[decision.decision_id]=fingerprint;self._event(record,"interrupt_decided",actor.subject);return self._view(record,False)
 def events_after(self,actor:Actor,cursor:int)->tuple[dict[str,object],...]:
  self._scope(actor,actor.tenant_id);events=[]
  for record in self.records.values():
   if record.request.tenant_id==actor.tenant_id:events.extend(event for event in record.events if int(event["cursor"])>cursor)
  return tuple(sorted(events,key=lambda event:int(event["cursor"])))
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise InterruptDenied("authenticated tenant scope required")
 def _event(self,record:InterruptRecord,event_type:str,actor_id:str)->None:
  self.cursor+=1;record.events.append({"cursor":self.cursor,"event_type":event_type,"interrupt_id":record.request.interrupt_id,"kind":record.request.kind,"status":record.status,"actor_id_sha256":_digest(actor_id),"checkpoint_id_sha256":_digest(record.request.checkpoint_id)})
 def _view(self,record:InterruptRecord,idempotent:bool)->dict[str,object]:return {"interrupt_id":record.request.interrupt_id,"status":record.status,"version":record.version,"decision_fingerprint":record.decision_fingerprint,"idempotent_replay":idempotent}
