from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from typing import Literal
class RemoteSupportDenied(ValueError):pass
@dataclass(frozen=True)
class RemoteAccessRequest:
 request_id:str;tenant_id:str;incident_id:str;employee_id:str;device_id:str;support_actor_id:str;capabilities:frozenset[Literal["view_screen","control_pointer","use_support_ui"]];expires_at:int;purpose:str
@dataclass(frozen=True)
class EmployeeDecision:request_id:str;employee_id:str;decision:Literal["allow","decline"];decided_at:int
@dataclass
class RemoteSession:
 session_id:str;tenant_id:str;incident_id:str;employee_id:str;device_id:str;support_actor_id:str;capabilities:frozenset[str];expires_at:int;status:Literal["active","declined","revoked","expired","ended"];events:list[str]=field(default_factory=list)
class RemoteSupportStore:
 def __init__(self)->None:self.requests:dict[str,RemoteAccessRequest]={};self.sessions:dict[str,RemoteSession]={}
 def request(self,value:RemoteAccessRequest,*,now:int)->RemoteAccessRequest:
  if not all((value.request_id,value.tenant_id,value.incident_id,value.employee_id,value.device_id,value.support_actor_id,value.purpose.strip())):raise RemoteSupportDenied("complete scoped request required")
  if value.request_id in self.requests or value.expires_at<=now or value.expires_at-now>900:raise RemoteSupportDenied("invalid request lifetime or replay")
  if not value.capabilities or not value.capabilities<=frozenset({"view_screen","control_pointer","use_support_ui"}):raise RemoteSupportDenied("invalid capabilities")
  self.requests[value.request_id]=value;return value
 def decide(self,decision:EmployeeDecision,*,now:int)->RemoteSession:
  request=self.requests.get(decision.request_id)
  if not request or request.employee_id!=decision.employee_id or decision.decided_at!=now or request.expires_at<=now:raise RemoteSupportDenied("decision scope or expiry mismatch")
  session_id=hashlib.sha256(json.dumps((request.request_id,decision.employee_id,decision.decision,now),separators=(",",":")).encode()).hexdigest()
  status="active" if decision.decision=="allow" else "declined";session=RemoteSession(session_id,request.tenant_id,request.incident_id,request.employee_id,request.device_id,request.support_actor_id,request.capabilities,request.expires_at,status,[f"employee_{decision.decision}"]);self.sessions[session_id]=session;return session
 def authorize_ui(self,session_id:str,*,tenant_id:str,incident_id:str,device_id:str,capability:str,now:int)->RemoteSession:
  session=self.sessions.get(session_id)
  if not session or session.status!="active" or session.expires_at<=now:raise RemoteSupportDenied("remote session inactive")
  if (session.tenant_id,session.incident_id,session.device_id)!=(tenant_id,incident_id,device_id) or capability not in session.capabilities:raise RemoteSupportDenied("remote session scope denied")
  session.events.append(f"authorized:{capability}");return session
 def revoke(self,session_id:str,employee_id:str)->None:
  session=self.sessions.get(session_id)
  if not session or session.employee_id!=employee_id:raise RemoteSupportDenied("revocation denied")
  session.status="revoked";session.events.append("employee_revoked")
 def end(self,session_id:str,support_actor_id:str)->None:
  session=self.sessions.get(session_id)
  if not session or session.support_actor_id!=support_actor_id:raise RemoteSupportDenied("end denied")
  session.status="ended";session.events.append("support_ended")
