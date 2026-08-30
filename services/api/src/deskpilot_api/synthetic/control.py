from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any,Mapping
from .digital_twin import DigitalTwin,TwinAction

@dataclass(frozen=True,slots=True)
class OperatorContext:
 subject:str
 roles:frozenset[str]
 tenant_ref:str
 is_ai:bool=False

@dataclass(frozen=True,slots=True)
class ScenarioDefinition:
 id:str
 title:str
 domain:str
 path:tuple[str|int,...]
 fault_value:Any
 risk:str

class SyntheticControlService:
 def __init__(self,twin:DigitalTwin,scenarios:Mapping[str,ScenarioDefinition],*,tenant_id:str="tenant-demo-kw",synthetic_mode:bool=False)->None:
  if not synthetic_mode:raise ValueError("synthetic control requires explicit synthetic mode")
  self._twin=twin;self._scenarios=dict(scenarios);self._tenant_id=tenant_id;self._snapshots:dict[str,dict[str,Any]]={};self._audit:list[dict[str,Any]]=[]
 def _authorize(self,operator:OperatorContext)->None:
  if operator.is_ai or operator.tenant_ref!=self._tenant_id or "tenant_administrator" not in operator.roles:raise PermissionError("synthetic operator access denied")
 def state(self,operator:OperatorContext)->dict[str,Any]:self._authorize(operator);snap=self._twin.snapshot();return {k:snap[k] for k in ("generation","version","digest")}|{"scenarios":[{"id":s.id,"title":s.title,"risk":s.risk} for s in self._scenarios.values()]}
 def capture_snapshot(self,operator:OperatorContext)->str:
  self._authorize(operator)
  if len(self._snapshots)>=50:raise ValueError("snapshot limit reached")
  snap=self._twin.snapshot();snapshot_id=f"snapshot-{snap['generation']}-{snap['version']}-{snap['digest'][:12]}";self._snapshots[snapshot_id]=snap;return snapshot_id
 def activate(self,operator:OperatorContext,scenario_id:str,*,expected_version:int)->dict[str,Any]:
  self._authorize(operator);scenario=self._scenarios.get(scenario_id)
  if scenario is None:raise ValueError("unknown synthetic scenario")
  before=self.capture_snapshot(operator);entry=self._twin.apply(TwinAction(scenario.domain,scenario.path,copy.deepcopy(scenario.fault_value),expected_version,scenario.id));self._record(operator,"activate",scenario.id,entry.resulting_digest);return {"snapshot_id":before,"version":self._twin.version,"digest":entry.resulting_digest}
 def rollback(self,operator:OperatorContext,*,expected_version:int)->dict[str,Any]:
  self._authorize(operator);entry=self._twin.rollback(expected_version=expected_version);self._record(operator,"rollback",entry.action.fault_type,entry.resulting_digest);return {"version":self._twin.version,"digest":entry.resulting_digest}
 def reset(self,operator:OperatorContext,confirmation:str)->dict[str,Any]:
  self._authorize(operator)
  if confirmation!="RESET SYNTHETIC TENANT":raise ValueError("reset confirmation mismatch")
  self._twin.reset();self._snapshots.clear();self._record(operator,"reset","baseline",self._twin.digest());return {"generation":self._twin.generation,"version":self._twin.version,"digest":self._twin.digest()}
 def compare(self,operator:OperatorContext,left_id:str,right_id:str)->dict[str,Any]:
  self._authorize(operator);left=self._snapshots[left_id];right=self._snapshots[right_id];return {"left_digest":left["digest"],"right_digest":right["digest"],"changed":left["digest"]!=right["digest"],"version_delta":right["version"]-left["version"]}
 def _record(self,operator:OperatorContext,action:str,target:str,digest:str)->None:self._audit.append({"sequence":len(self._audit)+1,"actor":operator.subject,"action":action,"target":target,"digest":digest})
