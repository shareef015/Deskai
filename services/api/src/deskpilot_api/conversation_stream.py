from __future__ import annotations
import hashlib,json,re
from dataclasses import dataclass,field
from typing import Literal
MAX_MESSAGES=100;MAX_MESSAGE_CHARS=4000;MAX_DELTA_CHARS=512
SECRET=re.compile(r"(?i)(password|passcode|api[_ -]?key|secret)\s*[:=]\s*\S+")
class ConversationDenied(ValueError):pass
@dataclass(frozen=True)
class Actor:subject:str;tenant_id:str;authenticated:bool
@dataclass(frozen=True)
class SendCommand:command_id:str;tenant_id:str;incident_id:str;thread_id:str;message_id:str;content:str;expected_cursor:int
@dataclass(frozen=True)
class ConversationEvent:
 cursor:int;event_id:str;event_type:Literal["message","assistant_start","assistant_delta","assistant_complete","assistant_stopped","error"];message_id:str;role:Literal["employee","assistant","system"];content:str;final:bool
@dataclass
class Conversation:
 tenant_id:str;incident_id:str;thread_id:str;employee_id:str;cursor:int=0;stopped:bool=False;commands:dict[str,str]=field(default_factory=dict);events:list[ConversationEvent]=field(default_factory=list)
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
def _safe(text:str)->str:return SECRET.sub("[REDACTED]",text.strip())
class ConversationStore:
 def __init__(self)->None:self.rows:dict[tuple[str,str,str],Conversation]={}
 def open(self,actor:Actor,tenant_id:str,incident_id:str,thread_id:str)->Conversation:
  self._scope(actor,tenant_id);key=(tenant_id,incident_id,thread_id);row=self.rows.get(key)
  if row and row.employee_id!=actor.subject:raise ConversationDenied("employee binding mismatch")
  if not row:row=Conversation(tenant_id,incident_id,thread_id,actor.subject);self.rows[key]=row
  return row
 def send(self,actor:Actor,command:SendCommand)->dict[str,object]:
  row=self.open(actor,command.tenant_id,command.incident_id,command.thread_id);fingerprint=_digest(command.__dict__)
  if command.command_id in row.commands:
   if row.commands[command.command_id]!=fingerprint:raise ConversationDenied("idempotency conflict")
   return self._view(row,True)
  if row.stopped:raise ConversationDenied("conversation stopped")
  if command.expected_cursor!=row.cursor:raise ConversationDenied("cursor concurrency mismatch")
  content=_safe(command.content)
  if not content or len(content)>MAX_MESSAGE_CHARS:raise ConversationDenied("message length invalid")
  self._append(row,"message",command.message_id,"employee",content,True);row.commands[command.command_id]=fingerprint;return self._view(row,False)
 def assistant_delta(self,row:Conversation,message_id:str,content:str,*,final:bool=False)->ConversationEvent:
  if row.stopped:raise ConversationDenied("conversation stopped")
  safe=_safe(content)
  if not safe or len(safe)>MAX_DELTA_CHARS:raise ConversationDenied("delta length invalid")
  return self._append(row,"assistant_complete" if final else "assistant_delta",message_id,"assistant",safe,final)
 def stop(self,actor:Actor,tenant_id:str,incident_id:str,thread_id:str)->ConversationEvent:
  row=self.open(actor,tenant_id,incident_id,thread_id)
  if row.stopped:return row.events[-1]
  row.stopped=True;return self._append(row,"assistant_stopped","system-stop","system","Support conversation stopped at the employee's request.",True)
 def after(self,actor:Actor,tenant_id:str,incident_id:str,thread_id:str,cursor:int)->tuple[ConversationEvent,...]:
  row=self.open(actor,tenant_id,incident_id,thread_id);return tuple(event for event in row.events if event.cursor>cursor)
 def _append(self,row:Conversation,event_type:str,message_id:str,role:str,content:str,final:bool)->ConversationEvent:
  row.cursor+=1;payload=(row.tenant_id,row.incident_id,row.thread_id,row.cursor,event_type,message_id,role,content,final);event=ConversationEvent(row.cursor,_digest(payload),event_type,message_id,role,content,final);row.events.append(event);row.events[:]=row.events[-MAX_MESSAGES:];return event
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise ConversationDenied("authenticated tenant scope required")
 def _view(self,row:Conversation,idempotent:bool)->dict[str,object]:return {"cursor":row.cursor,"stopped":row.stopped,"idempotent_replay":idempotent}
