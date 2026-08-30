from __future__ import annotations
import copy,hashlib,json
from dataclasses import dataclass
from typing import Any,Iterable

class StateConflict(ValueError): pass

@dataclass(frozen=True,slots=True)
class TwinAction:
 domain:str
 path:tuple[str|int,...]
 value:Any
 expected_version:int
 fault_type:str

@dataclass(frozen=True,slots=True)
class JournalEntry:
 sequence:int
 action:TwinAction
 previous_value:Any
 resulting_digest:str

class DigitalTwin:
 def __init__(self,baseline:dict[str,Any],*,tenant_id:str="tenant-demo-kw",synthetic_mode:bool=True)->None:
  if not synthetic_mode or baseline.get("tenant_id")!=tenant_id:raise ValueError("synthetic tenant baseline required")
  self._baseline=copy.deepcopy(baseline);self._state=copy.deepcopy(baseline);self._tenant_id=tenant_id;self._version=0;self._generation=1;self._journal:list[JournalEntry]=[]
 @property
 def version(self)->int:return self._version
 @property
 def generation(self)->int:return self._generation
 @property
 def journal(self)->tuple[JournalEntry,...]:return tuple(self._journal)
 def snapshot(self)->dict[str,Any]:return {"generation":self._generation,"version":self._version,"digest":self.digest(),"state":copy.deepcopy(self._state)}
 def digest(self)->str:return hashlib.sha256(json.dumps(self._state,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
 def apply(self,action:TwinAction)->JournalEntry:
  if action.expected_version!=self._version:raise StateConflict("digital twin state version conflict")
  if not action.fault_type or len(action.path)>12 or action.domain not in self._state:raise ValueError("fault action is not allowlisted")
  target=self._state[action.domain];previous=copy.deepcopy(_get(target,action.path));_set(target,action.path,copy.deepcopy(action.value));self._version+=1
  entry=JournalEntry(self._version,action,previous,self.digest());self._journal.append(entry);return entry
 def rollback(self,*,expected_version:int)->JournalEntry:
  if expected_version!=self._version:raise StateConflict("digital twin state version conflict")
  if not self._journal:raise ValueError("no action available for rollback")
  previous_entry=self._journal.pop();target=self._state[previous_entry.action.domain];current=copy.deepcopy(_get(target,previous_entry.action.path));_set(target,previous_entry.action.path,copy.deepcopy(previous_entry.previous_value));self._version+=1
  rollback_action=TwinAction(previous_entry.action.domain,previous_entry.action.path,previous_entry.previous_value,expected_version,f"rollback:{previous_entry.action.fault_type}")
  entry=JournalEntry(self._version,rollback_action,current,self.digest());self._journal.append(entry);return entry
 def reset(self)->None:self._state=copy.deepcopy(self._baseline);self._journal.clear();self._version=0;self._generation+=1
 def replay(self,actions:Iterable[TwinAction])->str:
  sequence=tuple(actions)
  if len(sequence)>100:raise ValueError("replay action limit exceeded")
  for action in sequence:self.apply(action)
  return self.digest()

def _get(root:Any,path:tuple[str|int,...])->Any:
 value=root
 for key in path:value=value[key]
 return value
def _set(root:Any,path:tuple[str|int,...],value:Any)->None:
 if not path:raise ValueError("state path cannot be empty")
 target=root
 for key in path[:-1]:target=target[key]
 target[path[-1]]=value
