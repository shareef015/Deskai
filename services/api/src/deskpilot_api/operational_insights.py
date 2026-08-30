from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from datetime import datetime,timezone
from typing import Literal
class InsightDenied(ValueError):pass
MetricKind=Literal["sla_aging","incident_volume","recovery_rate","rag_quality","agent_latency"]
@dataclass(frozen=True)
class MetricPoint:timestamp:str;value:float;dimension:str="all"
@dataclass(frozen=True)
class MetricSeries:metric:MetricKind;unit:str;points:tuple[MetricPoint,...]
@dataclass(frozen=True)
class InsightContext:tenant_id:str;mode:Literal["live","synthetic"];roles:frozenset[str];window_start:str;window_end:str
@dataclass(frozen=True)
class InsightSnapshot:tenant_id:str;mode:str;series:tuple[MetricSeries,...];generated_at:str;fingerprint:str
ALLOWED=frozenset({"service_desk_engineer","operations_viewer","demo_operator"});UNITS={"sla_aging":"incidents","incident_volume":"incidents","recovery_rate":"percent","rag_quality":"percent","agent_latency":"milliseconds"}
def _time(value:str)->datetime:
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
 except ValueError as exc:raise InsightDenied("invalid timestamp") from exc
def build_snapshot(context:InsightContext,series:tuple[MetricSeries,...],generated_at:str)->InsightSnapshot:
 if not context.tenant_id or not context.roles.intersection(ALLOWED):raise InsightDenied("authorized tenant context required")
 start,end,generated=_time(context.window_start),_time(context.window_end),_time(generated_at)
 if start>=end or (end-start).days>90 or generated<end:raise InsightDenied("invalid metric window")
 if not series or len(series)>10:raise InsightDenied("bounded metric series required")
 seen:set[str]=set();normalized=[]
 for item in series:
  if item.metric in seen or item.unit!=UNITS[item.metric] or not item.points or len(item.points)>100:raise InsightDenied("invalid metric series")
  seen.add(item.metric);points=tuple(sorted(item.points,key=lambda point:(point.timestamp,point.dimension)))
  for point in points:
   observed=_time(point.timestamp)
   if observed<start or observed>end or point.value<0 or point.value!=point.value:raise InsightDenied("invalid metric point")
   if item.unit=="percent" and point.value>100:raise InsightDenied("percent out of range")
  normalized.append(MetricSeries(item.metric,item.unit,points))
 ordered=tuple(sorted(normalized,key=lambda item:item.metric));payload={"tenant":context.tenant_id,"mode":context.mode,"start":context.window_start,"end":context.window_end,"series":[{"metric":item.metric,"unit":item.unit,"points":[point.__dict__ for point in item.points]} for item in ordered]};digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest();return InsightSnapshot(context.tenant_id,context.mode,ordered,generated_at,digest)
