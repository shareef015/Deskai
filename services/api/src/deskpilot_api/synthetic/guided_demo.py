from __future__ import annotations
import copy
from dataclasses import dataclass
from threading import RLock
from typing import Any

@dataclass(frozen=True,slots=True)
class DemoOperator:
 subject:str
 roles:frozenset[str]
 tenant_id:str
 is_ai:bool=False

class GuidedDemoService:
 _allowed=frozenset({"service_desk_engineer","tenant_administrator"})
 def __init__(self,dataset:dict[str,Any],*,tenant_id:str="tenant-demo-kw",synthetic_mode:bool=True)->None:
  if not synthetic_mode or not dataset.get("synthetic_only") or dataset.get("tenant_id")!=tenant_id:raise ValueError("synthetic demo dataset required")
  self._tenant_id=tenant_id;self._packs={p["pack_id"]:copy.deepcopy(p) for p in dataset["packs"]};self._sessions:dict[str,dict[str,Any]]={};self._lock=RLock()
 def _authorize(self,operator:DemoOperator)->None:
  if operator.is_ai or operator.tenant_id!=self._tenant_id or not operator.roles.intersection(self._allowed):raise PermissionError("guided demo operator denied")
 def catalog(self,operator:DemoOperator)->dict[str,Any]:
  self._authorize(operator);return {"synthetic_only":True,"packs":[{"pack_id":p["pack_id"],"title":p["title"],"theme":p["theme"],"estimated_minutes":p["estimated_minutes"]} for p in sorted(self._packs.values(),key=lambda p:p["order"])]}
 def start(self,operator:DemoOperator,pack_id:str)->dict[str,Any]:
  self._authorize(operator)
  if pack_id not in self._packs:raise ValueError("unknown curated demo pack")
  with self._lock:self._sessions[operator.subject]={"pack_id":pack_id,"step_index":0,"state":"running","generation":self._sessions.get(operator.subject,{}).get("generation",0)+1};return self.state(operator)
 def advance(self,operator:DemoOperator)->dict[str,Any]:
  self._authorize(operator)
  with self._lock:
   session=self._sessions.get(operator.subject)
   if not session or session["state"]!="running":raise ValueError("running demo session required")
   count=len(self._packs[session["pack_id"]]["steps"]);session["step_index"]+=1
   if session["step_index"]>=count:session["step_index"]=count-1;session["state"]="completed"
   return self.state(operator)
 def reset(self,operator:DemoOperator,confirmation:str)->dict[str,Any]:
  self._authorize(operator)
  if confirmation!="RESET GUIDED DEMO":raise ValueError("exact reset confirmation required")
  with self._lock:generation=self._sessions.get(operator.subject,{}).get("generation",0)+1;self._sessions[operator.subject]={"pack_id":None,"step_index":0,"state":"ready","generation":generation};return self.state(operator)
 def state(self,operator:DemoOperator)->dict[str,Any]:
  self._authorize(operator);session=copy.deepcopy(self._sessions.get(operator.subject,{"pack_id":None,"step_index":0,"state":"ready","generation":1}));pack=self._packs.get(session["pack_id"])
  return {**session,"synthetic_only":True,"pack":copy.deepcopy(pack),"current_step":copy.deepcopy(pack["steps"][session["step_index"]]) if pack else None}
