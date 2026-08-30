from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from typing import Literal
class GateDenied(ValueError):pass
@dataclass(frozen=True)
class Actor:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Evaluation:
 run_id:str;tenant_id:str;mode:Literal["offline","online","synthetic"];release_id:str;dataset_sha256:str;config_sha256:str;metrics:dict[str,float];slices:dict[str,dict[str,float]];evidence_ids:tuple[str,...];run_sha256:str
@dataclass(frozen=True)
class GatePolicy:minimums:dict[str,float];maximum_regression:dict[str,float];blocking_metrics:frozenset[str]
@dataclass
class ReleaseGate:release_id:str;tenant_id:str;baseline:Evaluation;candidate:Evaluation;status:str;blockers:tuple[dict[str,object],...];approval_sha256:str|None=None
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
class GateStore:
 def __init__(self)->None:self.gates:dict[str,ReleaseGate]={}
 def evaluate(self,actor:Actor,baseline:Evaluation,candidate:Evaluation,policy:GatePolicy)->ReleaseGate:
  self._scope(actor,candidate.tenant_id)
  if not actor.roles.intersection({"ai_engineer","release_manager","evaluator"}):raise GateDenied("evaluation role denied")
  if baseline.tenant_id!=candidate.tenant_id or baseline.mode!=candidate.mode:raise GateDenied("baseline scope mismatch")
  for run in (baseline,candidate):
   if not run.evidence_ids or run.run_sha256!=_digest({**run.__dict__,"run_sha256":""}):raise GateDenied("evaluation provenance invalid")
   if any(not 0<=value<=1 for value in run.metrics.values()):raise GateDenied("metric out of range")
  blockers=[]
  for metric,minimum in policy.minimums.items():
   value=candidate.metrics.get(metric,0)
   if value<minimum:blockers.append({"metric":metric,"class":"threshold","severity":"blocker" if metric in policy.blocking_metrics else "warning","value":value,"limit":minimum})
  for metric,budget in policy.maximum_regression.items():
   delta=baseline.metrics.get(metric,0)-candidate.metrics.get(metric,0)
   if delta>budget:blockers.append({"metric":metric,"class":"regression","severity":"blocker" if metric in policy.blocking_metrics else "warning","value":delta,"limit":budget})
  status="blocked" if any(item["severity"]=="blocker" for item in blockers) else "review";gate=ReleaseGate(candidate.release_id,candidate.tenant_id,baseline,candidate,status,tuple(blockers));self.gates[candidate.release_id]=gate;return gate
 def approve(self,actor:Actor,release_id:str,expected_run_sha256:str)->ReleaseGate:
  gate=self.gates.get(release_id)
  if not gate:raise GateDenied("gate not found")
  self._scope(actor,gate.tenant_id)
  if "release_approver" not in actor.roles or gate.status!="review":raise GateDenied("approval denied")
  if expected_run_sha256!=gate.candidate.run_sha256:raise GateDenied("evaluation concurrency mismatch")
  gate.status="approved";gate.approval_sha256=_digest((actor.subject,release_id,expected_run_sha256));return gate
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise GateDenied("authenticated tenant scope required")
