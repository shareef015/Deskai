from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from typing import Literal
SAFE_REOPEN=frozenset({"regression","employee_reports_recurrence","verification_defect","new_related_symptom"})
class ClosureDenied(ValueError):pass
@dataclass(frozen=True)
class Actor:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class ClosureRequest:
 closure_id:str;tenant_id:str;incident_id:str;checkpoint_id:str;actor_id:str;technical_checks:dict[str,bool];employee_confirmation:Literal["fixed","not_fixed"];resolution_summary:str;evidence_ids:tuple[str,...];resolved_at:str;sla_due_at:str;knowledge_candidate_id:str|None
@dataclass(frozen=True)
class ClosureRecord:closure_id:str;tenant_id:str;incident_id:str;checkpoint_id:str;summary:str;evidence_ids:tuple[str,...];sla_outcome:Literal["met","breached"];closed_at:str;closure_sha256:str
@dataclass(frozen=True)
class AuditEvent:event_id:str;event_type:str;actor_sha256:str;occurred_at:str;payload_sha256:str
@dataclass
class Incident:
 tenant_id:str;incident_id:str;status:str="active";closure:ClosureRecord|None=None;reopen_reason:str|None=None;audit:list[AuditEvent]=field(default_factory=list)
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
class ClosureStore:
 def __init__(self)->None:self.rows:dict[tuple[str,str],Incident]={}
 def close(self,actor:Actor,request:ClosureRequest)->ClosureRecord:
  self._scope(actor,request.tenant_id)
  if actor.subject!=request.actor_id or not actor.roles.intersection({"service_desk_engineer","operator","resolver"}):raise ClosureDenied("closure authority denied")
  row=self.rows.setdefault((request.tenant_id,request.incident_id),Incident(request.tenant_id,request.incident_id))
  if row.status=="closed":raise ClosureDenied("immutable closure already exists")
  if not request.technical_checks or not all(request.technical_checks.values()):raise ClosureDenied("technical verification incomplete")
  if request.employee_confirmation!="fixed":raise ClosureDenied("employee confirmation required")
  if not request.resolution_summary.strip() or not request.evidence_ids:raise ClosureDenied("summary and evidence required")
  sla="met" if request.resolved_at<=request.sla_due_at else "breached";payload={**request.__dict__,"actor_id":_digest(request.actor_id)}
  record=ClosureRecord(request.closure_id,request.tenant_id,request.incident_id,request.checkpoint_id,request.resolution_summary,request.evidence_ids,sla,request.resolved_at,_digest(payload));row.status="closed";row.closure=record;self._event(row,"closed",actor,request.resolved_at,record.closure_sha256);return record
 def reopen(self,actor:Actor,tenant_id:str,incident_id:str,reason:str,occurred_at:str,regression_evidence_ids:tuple[str,...])->Incident:
  self._scope(actor,tenant_id);row=self.rows.get((tenant_id,incident_id))
  if not row or row.status!="closed":raise ClosureDenied("closed incident required")
  if reason not in SAFE_REOPEN or not regression_evidence_ids:raise ClosureDenied("governed reopen reason and evidence required")
  row.status="reopened";row.reopen_reason=reason;self._event(row,"reopened",actor,occurred_at,_digest(regression_evidence_ids));return row
 def audit_export(self,actor:Actor,tenant_id:str,incident_id:str)->dict[str,object]:
  self._scope(actor,tenant_id)
  if not actor.roles.intersection({"operator","auditor","service_desk_engineer"}):raise ClosureDenied("audit export denied")
  row=self.rows.get((tenant_id,incident_id))
  if not row:raise ClosureDenied("incident not found")
  events=[event.__dict__ for event in row.audit];return {"incident_id":incident_id,"status":row.status,"closure":row.closure.__dict__ if row.closure else None,"events":events,"audit_sha256":_digest(events)}
 def _event(self,row:Incident,event_type:str,actor:Actor,occurred_at:str,payload:str)->None:row.audit.append(AuditEvent(_digest((row.incident_id,len(row.audit),event_type)),event_type,_digest(actor.subject),occurred_at,_digest(payload)))
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise ClosureDenied("authenticated tenant scope required")
