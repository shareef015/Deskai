from __future__ import annotations
import hashlib,json,re
from dataclasses import dataclass,field
from typing import Literal
class ActionDenied(ValueError):pass
ActionKind=Literal["diagnostic_consent","remediation_decision","handoff_note","employee_confirmation"]
@dataclass(frozen=True)
class ActionSchema:kind:ActionKind;required_fields:frozenset[str];allowed_fields:frozenset[str];maximum_length:int;required_role:str
@dataclass(frozen=True)
class ActionRequest:request_id:str;tenant_id:str;incident_id:str;actor_id:str;actor_roles:frozenset[str];kind:ActionKind;fields:dict[str,str];expected_fingerprint:str
@dataclass(frozen=True)
class ActionRecord:request_id:str;kind:ActionKind;status:Literal["accepted","rejected"];actor_sha256:str;payload_sha256:str;record_sha256:str
SCHEMAS={
 "diagnostic_consent":ActionSchema("diagnostic_consent",frozenset({"decision","scope"}),frozenset({"decision","scope","reason"}),500,"employee"),
 "remediation_decision":ActionSchema("remediation_decision",frozenset({"decision","plan_id"}),frozenset({"decision","plan_id","reason"}),1000,"remediation_approver"),
 "handoff_note":ActionSchema("handoff_note",frozenset({"note"}),frozenset({"note","team"}),2000,"service_desk_engineer"),
 "employee_confirmation":ActionSchema("employee_confirmation",frozenset({"outcome"}),frozenset({"outcome","comment"}),1000,"employee")}
SECRET=re.compile(r"(?i)(password|secret|token|api[_ -]?key)\s*[:=]\s*\S+")
def fingerprint(tenant_id:str,incident_id:str,kind:str)->str:return hashlib.sha256(f"{tenant_id}:{incident_id}:{kind}".encode()).hexdigest()
@dataclass
class ActionStore:
 records:dict[str,ActionRecord]=field(default_factory=dict)
 def submit(self,request:ActionRequest)->ActionRecord:
  schema=SCHEMAS.get(request.kind)
  if not schema or not request.tenant_id or not request.incident_id or not request.actor_id:raise ActionDenied("invalid action scope")
  if request.request_id in self.records:raise ActionDenied("duplicate submission")
  if schema.required_role not in request.actor_roles:raise ActionDenied("actor role denied")
  if request.expected_fingerprint!=fingerprint(request.tenant_id,request.incident_id,request.kind):raise ActionDenied("stale action context")
  keys=set(request.fields)
  if not schema.required_fields.issubset(keys) or not keys.issubset(schema.allowed_fields):raise ActionDenied("invalid action fields")
  clean={key:value.strip() for key,value in request.fields.items()}
  if any(not clean[key] for key in schema.required_fields) or any(len(value)>schema.maximum_length for value in clean.values()):raise ActionDenied("required or bounded field invalid")
  if any(SECRET.search(value) for value in clean.values()):raise ActionDenied("secret-like content denied")
  decision=clean.get("decision",clean.get("outcome","accepted"));status="rejected" if decision in {"reject","decline","not_fixed"} else "accepted"
  actor_sha=hashlib.sha256(request.actor_id.encode()).hexdigest();payload_sha=hashlib.sha256(json.dumps(clean,sort_keys=True,separators=(",",":")).encode()).hexdigest();record_sha=hashlib.sha256(f"{request.request_id}:{actor_sha}:{payload_sha}:{status}".encode()).hexdigest();record=ActionRecord(request.request_id,request.kind,status,actor_sha,payload_sha,record_sha);self.records[request.request_id]=record;return record
