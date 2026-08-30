from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from typing import Literal
MAX_QUEUE=500
class DashboardDenied(ValueError):pass
@dataclass(frozen=True)
class Viewer:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class IncidentRow:
 incident_id:str;tenant_id:str;mode:Literal["live","synthetic"];domain:Literal["outlook","printer","scanner","windows_network"];severity:Literal["low","medium","high","critical"];status:str;owner_type:Literal["agent","human","unassigned"];owner_label:str;created_at:str;sla_due_at:str;last_progress_at:str;pending_approval:bool;rollback_alert:bool
@dataclass(frozen=True)
class QueueEvent:cursor:int;tenant_id:str;mode:str;incident_id:str;event_type:str
def _time(value:str)->datetime:
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
 except ValueError as exc:raise DashboardDenied("invalid timestamp") from exc
class DashboardStore:
 def __init__(self)->None:self.rows:dict[str,IncidentRow]={};self.events:list[QueueEvent]=[];self.cursor=0
 def upsert(self,row:IncidentRow)->None:
  self.rows[row.incident_id]=row;self.cursor+=1;self.events.append(QueueEvent(self.cursor,row.tenant_id,row.mode,row.incident_id,"queue_changed"))
 def queue(self,viewer:Viewer,*,mode:str,now:str,domain:str|None=None,severity:str|None=None,owner_type:str|None=None)->tuple[dict[str,object],...]:
  self._scope(viewer);current=_time(now);result=[]
  for row in self.rows.values():
   if row.tenant_id!=viewer.tenant_id or row.mode!=mode:continue
   if domain and row.domain!=domain or severity and row.severity!=severity or owner_type and row.owner_type!=owner_type:continue
   age_minutes=max(0,int((current-_time(row.created_at)).total_seconds()//60));stalled=current>=_time(row.last_progress_at) and (current-_time(row.last_progress_at)).total_seconds()>=900
   result.append({**row.__dict__,"sla_state":"breached" if current>=_time(row.sla_due_at) else "at_risk" if (_time(row.sla_due_at)-current).total_seconds()<=900 else "healthy","age_minutes":age_minutes,"stalled":stalled})
  rank={"critical":0,"high":1,"medium":2,"low":3};return tuple(sorted(result,key=lambda item:(rank[str(item["severity"])],str(item["sla_due_at"]),str(item["incident_id"])))[:MAX_QUEUE])
 def summary(self,viewer:Viewer,mode:str,now:str)->dict[str,int]:
  rows=self.queue(viewer,mode=mode,now=now);return {"total":len(rows),"SLA_at_risk":sum(row["sla_state"]=="at_risk" for row in rows),"SLA_breached":sum(row["sla_state"]=="breached" for row in rows),"stalled":sum(bool(row["stalled"]) for row in rows),"approval_backlog":sum(bool(row["pending_approval"]) for row in rows),"rollback_alerts":sum(bool(row["rollback_alert"]) for row in rows),"human_owned":sum(row["owner_type"]=="human" for row in rows)}
 def events_after(self,viewer:Viewer,mode:str,cursor:int)->tuple[QueueEvent,...]:
  self._scope(viewer);return tuple(event for event in self.events if event.tenant_id==viewer.tenant_id and event.mode==mode and event.cursor>cursor)
 def _scope(self,viewer:Viewer)->None:
  if not viewer.authenticated or not viewer.roles.intersection({"operator","service_desk_engineer","manager","demo_operator"}):raise DashboardDenied("dashboard role denied")
