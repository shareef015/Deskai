from __future__ import annotations
import hashlib,json,re
from dataclasses import dataclass
from datetime import datetime,timezone
from typing import Literal
MAX_ITEMS=200;SAFE_DETAIL_KEYS=frozenset({"check","status","value_class","duration_ms","exit_class","error_code","correlation_id"})
SECRET=re.compile(r"(?i)(password|secret|token|api[_ -]?key)\s*[:=]\s*\S+")
class EvidenceDenied(ValueError):pass
@dataclass(frozen=True)
class Viewer:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Evidence:
 evidence_id:str;tenant_id:str;incident_id:str;kind:str;source:str;summary:str;observed_at:str;expires_at:str;digest:str;specialist_id:str;supervisor_handoff_id:str;contradiction_group:str|None;details:dict[str,object]
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
def _time(value:str)->datetime:
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
 except ValueError as exc:raise EvidenceDenied("invalid timestamp") from exc
def _safe(value:str)->str:return SECRET.sub("[REDACTED]",value)
class EvidenceStore:
 def __init__(self)->None:self.rows:dict[str,Evidence]={}
 def add(self,item:Evidence)->None:
  if item.evidence_id in self.rows:raise EvidenceDenied("immutable evidence already exists")
  if not set(item.details)<=SAFE_DETAIL_KEYS:raise EvidenceDenied("unsafe technical detail")
  if _time(item.expires_at)<=_time(item.observed_at):raise EvidenceDenied("invalid freshness window")
  canonical={**item.__dict__,"digest":""}
  if item.digest!=_digest(canonical):raise EvidenceDenied("evidence digest mismatch")
  if _safe(item.summary)!=item.summary:raise EvidenceDenied("unredacted secret")
  self.rows[item.evidence_id]=item
 def query(self,viewer:Viewer,incident_id:str,*,kind:str|None=None,source:str|None=None,contradictions_only:bool=False,now:str)->tuple[dict[str,object],...]:
  self._scope(viewer);current=_time(now);result=[]
  for item in self.rows.values():
   if item.tenant_id!=viewer.tenant_id or item.incident_id!=incident_id:continue
   if kind and item.kind!=kind or source and item.source!=source or contradictions_only and not item.contradiction_group:continue
   result.append(self._view(item,current))
  return tuple(sorted(result,key=lambda row:(str(row["observed_at"]),str(row["evidence_id"])),reverse=True)[:MAX_ITEMS])
 def export(self,viewer:Viewer,incident_id:str,selected_ids:tuple[str,...],*,now:str)->dict[str,object]:
  if not viewer.roles.intersection({"service_desk_engineer","operator","auditor"}):raise EvidenceDenied("export role denied")
  rows=self.query(viewer,incident_id,now=now);selected=[row for row in rows if row["evidence_id"] in set(selected_ids)]
  return {"schema_version":"1.0.0","tenant_id_sha256":_digest(viewer.tenant_id),"incident_id":incident_id,"evidence":selected,"export_sha256":_digest(selected)}
 def _view(self,item:Evidence,current:datetime)->dict[str,object]:
  return {"evidence_id":item.evidence_id,"kind":item.kind,"source":item.source,"summary":item.summary,"observed_at":item.observed_at,"freshness":"current" if current<_time(item.expires_at) else "stale","digest":item.digest,"specialist_id":item.specialist_id,"supervisor_handoff_id":item.supervisor_handoff_id,"contradiction_group":item.contradiction_group,"details":item.details}
 def _scope(self,viewer:Viewer)->None:
  if not viewer.authenticated:raise EvidenceDenied("authenticated viewer required")
