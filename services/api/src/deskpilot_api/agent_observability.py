from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
MAX_SPANS=1000;SAFE_FIELDS=frozenset({"node","agent","route","model_id","latency_ms","input_tokens","output_tokens","cost_microusd","tool_decision","error_class","retry_count","circuit_state","quality_score","drift_score","slo_status"})
class ObservabilityDenied(ValueError):pass
@dataclass(frozen=True)
class Viewer:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Span:
 span_id:str;trace_id:str;tenant_id:str;mode:Literal["live","synthetic"];incident_id:str;occurred_at:str;fields:dict[str,object]
class ObservabilityStore:
 def __init__(self)->None:self.spans:list[Span]=[]
 def add(self,span:Span)->None:
  if not set(span.fields)<=SAFE_FIELDS:raise ObservabilityDenied("unsafe trace field")
  if any(not isinstance(span.fields.get(key,0),(int,float)) or span.fields.get(key,0)<0 for key in ("latency_ms","input_tokens","output_tokens","cost_microusd","retry_count")):raise ObservabilityDenied("invalid metric")
  self.spans.append(span);self.spans[:]=self.spans[-MAX_SPANS:]
 def query(self,viewer:Viewer,mode:str,*,incident_id:str|None=None,agent:str|None=None)->tuple[Span,...]:
  self._scope(viewer);return tuple(span for span in self.spans if span.tenant_id==viewer.tenant_id and span.mode==mode and (not incident_id or span.incident_id==incident_id) and (not agent or span.fields.get("agent")==agent))
 def summary(self,viewer:Viewer,mode:str)->dict[str,object]:
  spans=self.query(viewer,mode);count=len(spans);latencies=[float(span.fields.get("latency_ms",0)) for span in spans];qualities=[float(span.fields["quality_score"]) for span in spans if "quality_score" in span.fields]
  return {"span_count":count,"average_latency_ms":round(sum(latencies)/count,2) if count else 0,"tokens":sum(int(span.fields.get("input_tokens",0))+int(span.fields.get("output_tokens",0)) for span in spans),"cost_microusd":sum(int(span.fields.get("cost_microusd",0)) for span in spans),"average_quality":round(sum(qualities)/len(qualities),3) if qualities else None,"SLO_alerts":sum(span.fields.get("slo_status")=="breach" for span in spans),"drift_alerts":sum(float(span.fields.get("drift_score",0))>=.2 for span in spans),"open_circuits":sum(span.fields.get("circuit_state")=="open" for span in spans)}
 def _scope(self,viewer:Viewer)->None:
  if not viewer.authenticated or not viewer.roles.intersection({"operator","ai_engineer","auditor","demo_operator"}):raise ObservabilityDenied("observability role denied")
