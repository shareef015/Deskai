from __future__ import annotations
import hashlib,json,uuid
from dataclasses import dataclass
from typing import Any,Literal,Mapping
from .migrations import CURRENT_STATE_VERSION,default_registry
from .state import validate_state

REPLAY_NAMESPACE=uuid.UUID("6c22f1d8-47d1-50d9-8a98-9d30b451182b");ALLOWED_ROLES=frozenset({"employee","service_desk_engineer","l2_l3_specialist","tenant_administrator"})
class ReplayDenied(PermissionError):pass
@dataclass(frozen=True,slots=True)
class ExecutionPrincipal:
 subject:str;tenant_id:str;roles:frozenset[str];is_ai:bool=False
@dataclass(frozen=True,slots=True)
class ReplayRequest:
 request_id:str;mode:Literal["resume","replay","fork"];tenant_id:str;incident_id:str;source_thread_id:str;source_run_id:str;source_checkpoint_id:str;source_checkpoint_sha256:str;configuration_fingerprint:str;target_state_version:str=CURRENT_STATE_VERSION

def payload_digest(payload:bytes)->str:return hashlib.sha256(payload).hexdigest()
def plan_execution(*,request:ReplayRequest,principal:ExecutionPrincipal,stored_scope:Mapping[str,str],state:Mapping[str,Any],serialized_checkpoint:bytes)->dict[str,Any]:
 if principal.is_ai or principal.tenant_id!=request.tenant_id or not principal.roles.intersection(ALLOWED_ROLES):raise ReplayDenied("execution principal denied")
 expected={"tenant_id":request.tenant_id,"incident_id":request.incident_id,"thread_id":request.source_thread_id,"run_id":request.source_run_id,"checkpoint_id":request.source_checkpoint_id,"configuration_fingerprint":request.configuration_fingerprint}
 if any(stored_scope.get(k)!=v for k,v in expected.items()):raise ReplayDenied("checkpoint scope or configuration mismatch")
 if payload_digest(serialized_checkpoint)!=request.source_checkpoint_sha256:raise ReplayDenied("checkpoint digest mismatch")
 migrated,events=default_registry().migrate(state,request.target_state_version)
 if validate_state(migrated):raise ReplayDenied("migrated graph state is invalid")
 new_execution=request.mode in {"replay","fork"};target_run_id=str(uuid.uuid5(REPLAY_NAMESPACE,f"run:{request.request_id}:{request.mode}:{request.source_run_id}")) if new_execution else request.source_run_id;target_thread_id=str(uuid.uuid5(REPLAY_NAMESPACE,f"thread:{request.request_id}:{request.mode}:{request.source_thread_id}")) if new_execution else request.source_thread_id
 pending=migrated.get("pending_interrupt");fresh_decision_required=new_execution and (pending is not None or migrated.get("phase") in {"consent","approval","confirmation"})
 if fresh_decision_required:migrated["pending_interrupt"]=None
 side_effect_policy="recorded_results_only" if request.mode=="replay" else "new_authorization_required" if request.mode=="fork" else "checkpoint_authorization_revalidated"
 provenance={"event_id":str(uuid.uuid5(REPLAY_NAMESPACE,f"event:{request.request_id}")),"request_id":request.request_id,"mode":request.mode,"tenant_id":request.tenant_id,"incident_id":request.incident_id,"source_run_id":request.source_run_id,"source_thread_id":request.source_thread_id,"source_checkpoint_id":request.source_checkpoint_id,"source_checkpoint_sha256":request.source_checkpoint_sha256,"target_run_id":target_run_id,"target_thread_id":target_thread_id,"configuration_fingerprint":request.configuration_fingerprint,"migration_events":events,"fresh_human_decision_required":fresh_decision_required,"side_effect_policy":side_effect_policy,"actor_id":principal.subject}
 provenance["provenance_sha256"]=hashlib.sha256(json.dumps(provenance,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
 return {"state":migrated,"target_run_id":target_run_id,"target_thread_id":target_thread_id,"fresh_human_decision_required":fresh_decision_required,"side_effect_policy":side_effect_policy,"provenance":provenance}

async def execute_time_travel(graph:Any,*,source_config:Mapping[str,Any],state_update:Mapping[str,Any]|None=None)->Any:
 config=dict(source_config)
 if state_update is not None:config=await graph.aupdate_state(config,dict(state_update))
 return await graph.ainvoke(None,config=config)
