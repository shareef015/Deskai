from __future__ import annotations
import asyncio,hashlib,json
from dataclasses import dataclass
from typing import Any,Awaitable,Callable,Literal
FailureCategory=Literal["timeout","rate_limited","dependency_unavailable","transient","validation","authorization","policy_denied","scope_violation","permanent","unknown"]
MAX_ATTEMPTS=3;MIN_TIMEOUT=1;MAX_TIMEOUT=60;DEFAULT_TIMEOUT=15;FAILURE_THRESHOLD=3;OPEN_SECONDS=30;HALF_OPEN_PROBES=1
RETRYABLE=frozenset({"timeout","rate_limited","dependency_unavailable","transient"});BACKOFF_SECONDS=(0,1,2)
class NodeFailure(RuntimeError):
 def __init__(self,category:FailureCategory,safe_message:str="Node execution failed",*,partial_mutation:bool=False):super().__init__(safe_message);self.category=category;self.safe_message=safe_message;self.partial_mutation=partial_mutation
class CircuitOpen(NodeFailure):
 def __init__(self):super().__init__("dependency_unavailable","Dependency circuit is open")
@dataclass(frozen=True)
class CircuitState:
 status:Literal["closed","open","half_open"]="closed";consecutive_failures:int=0;opened_at:float|None=None;half_open_probes:int=0
@dataclass(frozen=True)
class AttemptEvent:attempt:int;outcome:Literal["success","failure","timeout","circuit_open","compensated","compensation_failed"];category:FailureCategory|None;safe_message:str
@dataclass(frozen=True)
class ExecutionResult:
 status:Literal["succeeded","failed","compensated","escalated"];value:Any;events:tuple[AttemptEvent,...];circuit:CircuitState;provenance_sha256:str
def classify_exception(error:BaseException)->FailureCategory:
 if isinstance(error,NodeFailure):return error.category
 if isinstance(error,(TimeoutError,asyncio.TimeoutError)):return "timeout"
 return "unknown"
def circuit_before(state:CircuitState,now:float)->CircuitState:
 if state.status=="open" and state.opened_at is not None and now-state.opened_at>=OPEN_SECONDS:return CircuitState("half_open",state.consecutive_failures,state.opened_at,0)
 return state
def circuit_success(state:CircuitState)->CircuitState:return CircuitState()
def circuit_failure(state:CircuitState,now:float)->CircuitState:
 count=state.consecutive_failures+1
 if state.status=="half_open" or count>=FAILURE_THRESHOLD:return CircuitState("open",count,now,0)
 return CircuitState("closed",count,None,0)
def _provenance(node_name:str,events:tuple[AttemptEvent,...],circuit:CircuitState)->str:
 payload={"node":node_name,"events":[e.__dict__ for e in events],"circuit":circuit.__dict__};return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
async def execute_node(node_name:str,operation:Callable[[],Awaitable[Any]],*,circuit:CircuitState=CircuitState(),timeout_seconds:float=DEFAULT_TIMEOUT,now:Callable[[],float],sleep:Callable[[float],Awaitable[None]]=asyncio.sleep,compensate:Callable[[str],Awaitable[None]]|None=None,idempotency_key:str|None=None)->ExecutionResult:
 if not node_name:raise ValueError("node_name required")
 if not MIN_TIMEOUT<=timeout_seconds<=MAX_TIMEOUT:raise ValueError("invalid node timeout")
 current=circuit_before(circuit,now());events:list[AttemptEvent]=[]
 if current.status=="open":events.append(AttemptEvent(0,"circuit_open","dependency_unavailable","Dependency circuit is open"));return ExecutionResult("escalated",None,tuple(events),current,_provenance(node_name,tuple(events),current))
 if current.status=="half_open" and current.half_open_probes>=HALF_OPEN_PROBES:events.append(AttemptEvent(0,"circuit_open","dependency_unavailable","Half-open probe already used"));return ExecutionResult("escalated",None,tuple(events),current,_provenance(node_name,tuple(events),current))
 partial=False;last_category:FailureCategory="unknown"
 for attempt in range(1,MAX_ATTEMPTS+1):
  try:
   value=await asyncio.wait_for(operation(),timeout_seconds);events.append(AttemptEvent(attempt,"success",None,"Node execution succeeded"));current=circuit_success(current);return ExecutionResult("succeeded",value,tuple(events),current,_provenance(node_name,tuple(events),current))
  except asyncio.CancelledError:raise
  except BaseException as error:
   category=classify_exception(error);last_category=category;partial=partial or bool(getattr(error,"partial_mutation",False));outcome="timeout" if category=="timeout" else "failure";events.append(AttemptEvent(attempt,outcome,category,getattr(error,"safe_message","Node execution failed")));current=circuit_failure(current,now())
   if category not in RETRYABLE or attempt>=MAX_ATTEMPTS or current.status=="open":break
   await sleep(BACKOFF_SECONDS[attempt])
 if partial:
  if compensate is None or not idempotency_key:events.append(AttemptEvent(len(events)+1,"compensation_failed",last_category,"Compensation unavailable"));status="escalated"
  else:
   try:await compensate(idempotency_key);events.append(AttemptEvent(len(events)+1,"compensated",None,"Compensation succeeded"));status="compensated"
   except BaseException:events.append(AttemptEvent(len(events)+1,"compensation_failed",last_category,"Compensation failed"));status="escalated"
 else:status="failed"
 return ExecutionResult(status,None,tuple(events),current,_provenance(node_name,tuple(events),current))
