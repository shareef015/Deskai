from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any,Callable,Mapping

CURRENT_STATE_VERSION="1.0.0";IMMUTABLE_FIELDS=("tenant_id","incident_id","thread_id","correlation_id","employee_id","device_id");MAX_MIGRATION_STEPS=8
class StateMigrationError(ValueError):pass
MigrationFunction=Callable[[Mapping[str,Any]],dict[str,Any]]
@dataclass(frozen=True,slots=True)
class MigrationStep:
 source_version:str;target_version:str;upgrade:MigrationFunction;downgrade:MigrationFunction;description:str
class MigrationRegistry:
 def __init__(self)->None:self._steps:dict[str,MigrationStep]={}
 def register(self,step:MigrationStep)->None:
  if step.source_version in self._steps or step.source_version==step.target_version:raise StateMigrationError("duplicate or circular migration")
  self._steps[step.source_version]=step
 def path(self,source_version:str,target_version:str=CURRENT_STATE_VERSION)->tuple[MigrationStep,...]:
  if source_version==target_version:return ()
  result=[];current=source_version;visited=set()
  while current!=target_version:
   if current in visited or current not in self._steps or len(result)>=MAX_MIGRATION_STEPS:raise StateMigrationError("no contiguous migration path")
   visited.add(current);step=self._steps[current];result.append(step);current=step.target_version
  return tuple(result)
 def migrate(self,state:Mapping[str,Any],target_version:str=CURRENT_STATE_VERSION)->tuple[dict[str,Any],tuple[dict[str,str],...]]:
  original=copy.deepcopy(dict(state));version=str(original.get("state_version",""));working=copy.deepcopy(original);events=[]
  for step in self.path(version,target_version):working=step.upgrade(copy.deepcopy(working));working["state_version"]=step.target_version;events.append({"source_version":step.source_version,"target_version":step.target_version,"description":step.description})
  for field in IMMUTABLE_FIELDS:
   if working.get(field)!=original.get(field):raise StateMigrationError(f"migration changed immutable field {field}")
  return working,tuple(events)

def _upgrade_090(state:Mapping[str,Any])->dict[str,Any]:
 result=copy.deepcopy(dict(state));result["phase"]=result.pop("stage",result.get("phase","intake"));result.setdefault("pending_interrupt",None);result.setdefault("retry_counts",{});result.setdefault("errors",());result.setdefault("audit_event_ids",());return result
def _downgrade_100(state:Mapping[str,Any])->dict[str,Any]:
 result=copy.deepcopy(dict(state));result["stage"]=result.pop("phase",result.get("stage","intake"));result.pop("pending_interrupt",None);result["state_version"]="0.9.0";return result
def default_registry()->MigrationRegistry:
 registry=MigrationRegistry();registry.register(MigrationStep("0.9.0","1.0.0",_upgrade_090,_downgrade_100,"rename stage to phase and initialize durable interrupt/retry/error fields"));return registry
