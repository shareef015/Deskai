from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from datetime import datetime,timezone
from typing import Literal
SAFE_PACKET=frozenset({"summary","reason_code","severity","evidence_ids","attempted_action_ids","rollback_status","requested_team","verification_ids","employee_impact"})
class HandoffDenied(ValueError):pass
@dataclass(frozen=True)
class Actor:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Handoff:
 handoff_id:str;tenant_id:str;incident_id:str;thread_id:str;checkpoint_id:str;requester_id:str;owner_team:str;severity:Literal["low","medium","high","critical"];reason_code:str;created_at:str;sla_due_at:str;packet:dict[str,object];packet_sha256:str
@dataclass(frozen=True)
class CustodyEvent:event_id:str;event_type:str;actor_id_sha256:str;from_owner:str|None;to_owner:str|None;occurred_at:str;detail_sha256:str
@dataclass
class Case:
 handoff:Handoff;status:str="queued";owner_id:str|None=None;events:list[CustodyEvent]=field(default_factory=list);human_change_sha256:str|None=None;verification_required:bool=False
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
def _time(value:str)->datetime:
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
 except ValueError as exc:raise HandoffDenied("invalid timestamp") from exc
class HandoffStore:
 def __init__(self)->None:self.rows:dict[str,Case]={}
 def create(self,actor:Actor,handoff:Handoff)->Case:
  self._scope(actor,handoff.tenant_id)
  if actor.subject!=handoff.requester_id or not actor.roles.intersection({"service_desk_engineer","operator","system"}):raise HandoffDenied("requester denied")
  if handoff.handoff_id in self.rows or not set(handoff.packet)<=SAFE_PACKET:raise HandoffDenied("duplicate or unsafe handoff")
  if _time(handoff.sla_due_at)<=_time(handoff.created_at):raise HandoffDenied("invalid SLA")
  if handoff.packet_sha256!=_digest(handoff.packet):raise HandoffDenied("packet digest mismatch")
  case=Case(handoff);self.rows[handoff.handoff_id]=case;self._event(case,"queued",actor.subject,None,handoff.owner_team,handoff.packet_sha256,handoff.created_at);return case
 def queue(self,actor:Actor,team:str,now:str)->tuple[dict[str,object],...]:
  self._scope(actor,actor.tenant_id)
  if not actor.roles.intersection({"service_desk_engineer","operator","resolver"}):raise HandoffDenied("queue role denied")
  return tuple({"handoff_id":case.handoff.handoff_id,"severity":case.handoff.severity,"reason_code":case.handoff.reason_code,"status":case.status,"sla_state":"breached" if _time(now)>=_time(case.handoff.sla_due_at) else "within_sla"} for case in self.rows.values() if case.handoff.tenant_id==actor.tenant_id and case.handoff.owner_team==team)
 def acknowledge(self,actor:Actor,handoff_id:str,occurred_at:str)->Case:
  case=self._case(actor,handoff_id)
  if "resolver" not in actor.roles or case.status!="queued":raise HandoffDenied("acknowledgement denied")
  case.status="acknowledged";case.owner_id=actor.subject;self._event(case,"acknowledged",actor.subject,case.handoff.owner_team,actor.subject,"ack",occurred_at);return case
 def record_change(self,actor:Actor,handoff_id:str,change_summary:str,occurred_at:str)->Case:
  case=self._case(actor,handoff_id)
  if case.status!="acknowledged" or case.owner_id!=actor.subject:raise HandoffDenied("custody denied")
  case.human_change_sha256=_digest(change_summary);case.verification_required=True;case.status="verification_required";self._event(case,"human_change",actor.subject,actor.subject,actor.subject,case.human_change_sha256,occurred_at);return case
 def return_to_agent(self,actor:Actor,handoff_id:str,verification_ids:tuple[str,...],occurred_at:str)->Case:
  case=self._case(actor,handoff_id)
  if case.owner_id!=actor.subject or not case.verification_required or not verification_ids:raise HandoffDenied("verified return required")
  case.status="returned_for_verification";self._event(case,"returned_for_verification",actor.subject,actor.subject,"agent_supervisor",_digest(verification_ids),occurred_at);return case
 def _case(self,actor:Actor,handoff_id:str)->Case:
  case=self.rows.get(handoff_id)
  if not case:raise HandoffDenied("handoff not found")
  self._scope(actor,case.handoff.tenant_id);return case
 def _event(self,case:Case,event_type:str,actor:str,from_owner:str|None,to_owner:str|None,detail:str,occurred_at:str)->None:
  payload=(case.handoff.handoff_id,len(case.events)+1,event_type,actor,from_owner,to_owner,detail,occurred_at);case.events.append(CustodyEvent(_digest(payload),event_type,_digest(actor),from_owner,to_owner,occurred_at,_digest(detail)))
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise HandoffDenied("authenticated tenant scope required")
