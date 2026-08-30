from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from datetime import datetime,timezone
from typing import Literal

class AuthDenied(ValueError):pass
Mode=Literal["live","synthetic"]
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
@dataclass(frozen=True)
class OIDCClaims:
 subject:str;tenant_id:str;roles:frozenset[str];issuer:str;audience:str;auth_time:int;expires_at:int;session_id:str
@dataclass(frozen=True)
class Persona:
 persona_id:str;label:str;roles:frozenset[str];allowed_navigation:tuple[str,...]
@dataclass
class Session:
 session_id:str;subject:str;tenant_id:str;roles:frozenset[str];mode:Mode;expires_at:int;persona_id:str|None=None;revoked:bool=False
@dataclass(frozen=True)
class AuditEvent:
 event_type:str;session_sha256:str;actor_sha256:str;persona_sha256:str|None;occurred_at:int;event_sha256:str

class AuthStore:
 def __init__(self,*,issuer:str="https://identity.example.test",audience:str="deskpilot-api",production:bool=False)->None:
  self.issuer=issuer;self.audience=audience;self.production=production;self.sessions:dict[str,Session]={};self.audit:list[AuditEvent]=[]
  self.personas={
   "employee":Persona("employee","Employee",frozenset({"employee"}),("incident-workspace","conversation-workspace")),
   "service-desk":Persona("service-desk","Service desk engineer",frozenset({"service_desk_engineer"}),("incident-workspace","evidence-explorer","remediation-review","human-handoff")),
   "approver":Persona("approver","Remediation approver",frozenset({"remediation_approver"}),("remediation-review","execution-verification")),
   "operations":Persona("operations","Operations viewer",frozenset({"operations_viewer"}),("operations","agent-observability","evaluation-gates")),
  }
 def create_live_session(self,claims:OIDCClaims,*,now:int|None=None)->Session:
  now=self._now(now)
  if claims.issuer!=self.issuer or claims.audience!=self.audience:raise AuthDenied("OIDC issuer or audience denied")
  if not claims.subject or not claims.tenant_id or not claims.roles or claims.auth_time>now or claims.expires_at<=now:raise AuthDenied("invalid or expired OIDC claims")
  if claims.session_id in self.sessions:raise AuthDenied("session identifier already used")
  session=Session(claims.session_id,claims.subject,claims.tenant_id,claims.roles,"live",claims.expires_at);self.sessions[session.session_id]=session;self._event("live_session_created",session,now);return session
 def create_demo_session(self,claims:OIDCClaims,persona_id:str,*,now:int|None=None)->Session:
  now=self._now(now)
  if self.production:raise AuthDenied("synthetic persona sessions are disabled in production")
  if "demo_operator" not in claims.roles:raise AuthDenied("demo operator role required")
  self._validate_base_claims(claims,now);persona=self._persona(persona_id)
  session_id=_digest((claims.session_id,persona_id,now))
  if session_id in self.sessions:raise AuthDenied("demo session replay denied")
  session=Session(session_id,claims.subject,claims.tenant_id,persona.roles|frozenset({"demo_operator"}),"synthetic",min(claims.expires_at,now+1800),persona_id);self.sessions[session_id]=session;self._event("demo_session_created",session,now);return session
 def switch_demo_persona(self,actor_session_id:str,persona_id:str,*,now:int|None=None)->Session:
  now=self._now(now);actor=self.authorize(actor_session_id,mode="synthetic",now=now)
  if "demo_operator" not in actor.roles:raise AuthDenied("demo persona switching requires operator identity")
  persona=self._persona(persona_id);session_id=_digest((actor.session_id,persona_id,len(self.audit),now));session=Session(session_id,actor.subject,actor.tenant_id,persona.roles|frozenset({"demo_operator"}),"synthetic",actor.expires_at,persona_id);self.sessions[session_id]=session;self._event("demo_persona_switched",session,now);return session
 def authorize(self,session_id:str,*,tenant_id:str|None=None,required_role:str|None=None,mode:Mode|None=None,now:int|None=None)->Session:
  now=self._now(now);session=self.sessions.get(session_id)
  if not session or session.revoked or session.expires_at<=now:raise AuthDenied("session missing, revoked, or expired")
  if tenant_id is not None and tenant_id!=session.tenant_id:raise AuthDenied("tenant mismatch")
  if mode is not None and mode!=session.mode:raise AuthDenied("environment mode mismatch")
  if required_role is not None and required_role not in session.roles:raise AuthDenied("role denied")
  return session
 def navigation(self,session_id:str,*,now:int|None=None)->tuple[str,...]:
  session=self.authorize(session_id,now=now)
  if session.persona_id:return self._persona(session.persona_id).allowed_navigation
  grants={"employee":("incident-workspace","conversation-workspace"),"service_desk_engineer":("incident-workspace","evidence-explorer","remediation-review","human-handoff"),"remediation_approver":("remediation-review","execution-verification"),"operations_viewer":("operations","agent-observability","evaluation-gates")}
  return tuple(dict.fromkeys(path for role in sorted(session.roles) for path in grants.get(role,())))
 def logout(self,session_id:str,*,now:int|None=None)->None:
  now=self._now(now);session=self.sessions.get(session_id)
  if not session:raise AuthDenied("session not found")
  session.revoked=True;self._event("session_revoked",session,now)
 def _validate_base_claims(self,claims:OIDCClaims,now:int)->None:
  if claims.issuer!=self.issuer or claims.audience!=self.audience or not claims.subject or not claims.tenant_id or claims.auth_time>now or claims.expires_at<=now:raise AuthDenied("invalid OIDC claims")
 def _persona(self,persona_id:str)->Persona:
  persona=self.personas.get(persona_id)
  if not persona:raise AuthDenied("persona not allowed")
  return persona
 def _event(self,event_type:str,session:Session,now:int)->None:
  payload=(event_type,_digest(session.session_id),_digest(session.subject),_digest(session.persona_id) if session.persona_id else None,now,len(self.audit));fingerprint=_digest(payload);self.audit.append(AuditEvent(event_type,payload[1],payload[2],payload[3],now,fingerprint))
 @staticmethod
 def _now(value:int|None)->int:return value if value is not None else int(datetime.now(timezone.utc).timestamp())
