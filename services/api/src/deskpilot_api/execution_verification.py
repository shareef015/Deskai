from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from typing import Literal
TERMINAL=frozenset({"verified","rolled_back","human_recovery","cancelled"})
class ExecutionDenied(ValueError):pass
@dataclass(frozen=True)
class Principal:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class ExecutionToken:
 token_id:str;tenant_id:str;incident_id:str;device_id:str;plan_id:str;plan_sha256:str;capabilities:frozenset[str];expires_at:str;single_use:bool=True
@dataclass(frozen=True)
class ActionSpec:action_id:str;capability:str;pre_state_sha256:str;rollback_capability:str|None;verification_id:str
@dataclass(frozen=True)
class ActionResult:action_id:str;status:Literal["succeeded","failed","partial","timeout"];result_sha256:str;post_state_sha256:str|None
@dataclass
class Run:
 run_id:str;tenant_id:str;incident_id:str;device_id:str;plan_id:str;plan_sha256:str;token_id:str;actions:tuple[ActionSpec,...];status:str="running";results:dict[str,ActionResult]=field(default_factory=dict);rollback_results:dict[str,bool]=field(default_factory=dict);regression_checks:dict[str,bool]=field(default_factory=dict);employee_confirmation:str|None=None
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
class ExecutionStore:
 def __init__(self)->None:self.runs:dict[str,Run]={};self.used_tokens:set[str]=set()
 def start(self,principal:Principal,run_id:str,token:ExecutionToken,actions:tuple[ActionSpec,...],approved_plan_sha256:str)->Run:
  self._scope(principal,token.tenant_id)
  if not principal.roles.intersection({"executor","service_desk_engineer"}):raise ExecutionDenied("execution role denied")
  if token.token_id in self.used_tokens or run_id in self.runs:raise ExecutionDenied("duplicate execution denied")
  if token.plan_sha256!=approved_plan_sha256:raise ExecutionDenied("approved plan mismatch")
  if not actions or any(action.capability not in token.capabilities or not action.pre_state_sha256 for action in actions):raise ExecutionDenied("capability or pre-state mismatch")
  run=Run(run_id,token.tenant_id,token.incident_id,token.device_id,token.plan_id,token.plan_sha256,token.token_id,actions);self.runs[run_id]=run;self.used_tokens.add(token.token_id);return run
 def record(self,principal:Principal,run_id:str,result:ActionResult)->str:
  run=self._run(principal,run_id)
  if run.status in TERMINAL:raise ExecutionDenied("terminal run immutable")
  if result.action_id in run.results:raise ExecutionDenied("action result immutable")
  if result.action_id not in {action.action_id for action in run.actions}:raise ExecutionDenied("unknown action")
  run.results[result.action_id]=result
  if len(run.results)<len(run.actions):run.status="running";return run.status
  if all(value.status=="succeeded" for value in run.results.values()):run.status="verifying";return run.status
  failed=[action for action in run.actions if run.results[action.action_id].status!="succeeded"];run.status="rolling_back" if all(action.rollback_capability for action in failed) else "human_recovery";return run.status
 def rollback(self,principal:Principal,run_id:str,action_id:str,verified:bool)->str:
  run=self._run(principal,run_id)
  if run.status!="rolling_back":raise ExecutionDenied("rollback not active")
  failed=[action for action in run.actions if run.results[action.action_id].status!="succeeded"]
  if action_id not in {action.action_id for action in failed}:raise ExecutionDenied("rollback scope denied")
  run.rollback_results[action_id]=verified
  if len(run.rollback_results)==len(failed):run.status="rolled_back" if all(run.rollback_results.values()) else "human_recovery"
  return run.status
 def verify(self,principal:Principal,run_id:str,checks:dict[str,bool],employee_outcome:Literal["fixed","not_fixed"])->str:
  run=self._run(principal,run_id)
  if run.status!="verifying":raise ExecutionDenied("verification not active")
  required={action.verification_id for action in run.actions}
  if set(checks)!=required:raise ExecutionDenied("complete verification required")
  run.regression_checks=dict(checks);run.employee_confirmation=employee_outcome
  run.status="verified" if all(checks.values()) and employee_outcome=="fixed" else "human_recovery";return run.status
 def _run(self,principal:Principal,run_id:str)->Run:
  run=self.runs.get(run_id)
  if not run:raise ExecutionDenied("run not found")
  self._scope(principal,run.tenant_id);return run
 def _scope(self,principal:Principal,tenant_id:str)->None:
  if not principal.authenticated or principal.tenant_id!=tenant_id:raise ExecutionDenied("authenticated tenant scope required")
