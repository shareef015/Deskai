from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass,field
from typing import Literal

ALLOWED_EVENT_FIELDS=frozenset({"phase","status","agent_id","route_reason","interrupt_kind","decision_required","evidence_count","error_class","recovery_route","trace_head_sha256"})
TERMINAL_STATUSES=frozenset({"resolved","escalated","cancelled"})

class RuntimeDenied(ValueError):pass

@dataclass(frozen=True)
class Principal:
 subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool

@dataclass(frozen=True)
class Command:
 command_id:str;tenant_id:str;incident_id:str;thread_id:str;action:Literal["start","resume","cancel"];expected_checkpoint_id:str|None;decision_fingerprint:str|None;synthetic_demo:bool=False

@dataclass(frozen=True)
class TimelineEvent:
 cursor:int;event_id:str;tenant_id:str;incident_id:str;thread_id:str;event_type:Literal["graph","interrupt","decision","terminal","error"];public_fields:dict[str,object];event_sha256:str

@dataclass
class Execution:
 tenant_id:str;incident_id:str;thread_id:str;checkpoint_id:str;status:str="running";last_cursor:int=0;processed_commands:dict[str,str]=field(default_factory=dict);events:list[TimelineEvent]=field(default_factory=list)

def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()

class RuntimeStore:
 def __init__(self)->None:self.executions:dict[tuple[str,str,str],Execution]={}
 def apply(self,principal:Principal,command:Command)->dict[str,object]:
  if not principal.authenticated or principal.tenant_id!=command.tenant_id or not principal.roles.intersection({"employee","service_desk_engineer","operator","demo_operator"}):raise RuntimeDenied("authenticated tenant role required")
  if command.synthetic_demo and "demo_operator" not in principal.roles:raise RuntimeDenied("demo mode requires demo operator")
  key=(command.tenant_id,command.incident_id,command.thread_id);fingerprint=_digest(command.__dict__);execution=self.executions.get(key)
  if execution and command.command_id in execution.processed_commands:
   if execution.processed_commands[command.command_id]!=fingerprint:raise RuntimeDenied("idempotency conflict")
   return self._view(execution,True)
  if command.action=="start":
   if execution and execution.status not in TERMINAL_STATUSES:raise RuntimeDenied("execution already active")
   execution=Execution(command.tenant_id,command.incident_id,command.thread_id,"cp-"+fingerprint[:16]);self.executions[key]=execution;self._event(execution,"graph",{"phase":"greeting","status":"running"})
  elif not execution:raise RuntimeDenied("execution not found")
  elif execution.status in TERMINAL_STATUSES:raise RuntimeDenied("terminal execution is immutable")
  elif command.expected_checkpoint_id!=execution.checkpoint_id:raise RuntimeDenied("checkpoint concurrency mismatch")
  elif command.action=="resume":
   if not command.decision_fingerprint or len(command.decision_fingerprint)!=64:raise RuntimeDenied("validated decision fingerprint required")
   execution.checkpoint_id="cp-"+_digest((execution.checkpoint_id,command.decision_fingerprint))[:16];self._event(execution,"decision",{"phase":"resumed","status":"running"})
  else:
   execution.status="cancelled";self._event(execution,"terminal",{"phase":"cancelled","status":"cancelled"})
  execution.processed_commands[command.command_id]=fingerprint
  return self._view(execution,False)
 def _event(self,execution:Execution,event_type:str,fields:dict[str,object])->TimelineEvent:
  if not set(fields)<=ALLOWED_EVENT_FIELDS:raise RuntimeDenied("private event field prohibited")
  execution.last_cursor+=1;payload={"scope":(execution.tenant_id,execution.incident_id,execution.thread_id),"cursor":execution.last_cursor,"type":event_type,"fields":fields};event=TimelineEvent(execution.last_cursor,str(uuid.uuid5(uuid.NAMESPACE_URL,_digest(payload))),execution.tenant_id,execution.incident_id,execution.thread_id,event_type,fields,_digest(payload));execution.events.append(event);return event
 def stream(self,principal:Principal,tenant_id:str,incident_id:str,thread_id:str,after_cursor:int)->tuple[TimelineEvent,...]:
  if not principal.authenticated or principal.tenant_id!=tenant_id:raise RuntimeDenied("stream scope denied")
  execution=self.executions.get((tenant_id,incident_id,thread_id))
  if not execution:return ()
  return tuple(event for event in execution.events if event.cursor>after_cursor)
 def _view(self,execution:Execution,idempotent:bool)->dict[str,object]:return {"tenant_id":execution.tenant_id,"incident_id":execution.incident_id,"thread_id":execution.thread_id,"checkpoint_id":execution.checkpoint_id,"status":execution.status,"last_cursor":execution.last_cursor,"idempotent_replay":idempotent}

def encode_sse(event:TimelineEvent)->str:
 data=json.dumps({"event_id":event.event_id,"cursor":event.cursor,"event_type":event.event_type,"fields":event.public_fields,"event_sha256":event.event_sha256},sort_keys=True,separators=(",",":"))
 return f"id: {event.cursor}\nevent: {event.event_type}\ndata: {data}\n\n"
