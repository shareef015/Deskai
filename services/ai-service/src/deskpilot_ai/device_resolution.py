from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
MIN_CONFIDENCE=.8;MIN_MARGIN=.1;MAX_DISCLOSED=3
OS_VALUES=frozenset({"windows_10","windows_11"});RELATIONSHIPS=frozenset({"primary","assigned","shared"});BASE_SCORE={"primary":.95,"assigned":.85,"shared":.65}
class DeviceResolutionError(ValueError):pass
@dataclass(frozen=True)
class DeviceRelationship:
 tenant_id:str;employee_id:str;device_id:str;display_name:str;operating_system:str;relationship_type:str;relationship_id:str;active:bool;device_registered:bool;recently_seen:bool
@dataclass(frozen=True)
class DeviceCandidate:device_id:str;display_name:str;operating_system:str;confidence:float;relationship_id:str
@dataclass(frozen=True)
class ResolutionResult:
 outcome:Literal["pending_confirmation","ambiguous","not_found","confirmed","declined","escalated"];candidates:tuple[DeviceCandidate,...];selected_device_id:str|None;confirmation_token:str|None;reason:str;provenance_sha256:str
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def resolve_devices(*,tenant_id:str,employee_id:str,relationships:tuple[DeviceRelationship,...],reported_device_id:str|None)->ResolutionResult:
 eligible=[]
 for item in relationships:
  if item.tenant_id!=tenant_id:raise DeviceResolutionError("cross-tenant relationship returned")
  if item.employee_id!=employee_id or not item.active or not item.device_registered or item.operating_system not in OS_VALUES or item.relationship_type not in RELATIONSHIPS:continue
  score=1.0 if reported_device_id and item.device_id==reported_device_id else min(1.0,BASE_SCORE[item.relationship_type]+(.03 if item.recently_seen else 0))
  eligible.append(DeviceCandidate(item.device_id,item.display_name[:80],item.operating_system,score,item.relationship_id))
 eligible=sorted(eligible,key=lambda x:(-x.confidence,x.device_id))
 audit=[{"device_id":x.device_id,"relationship_id":x.relationship_id,"confidence":x.confidence} for x in eligible]
 if not eligible:return ResolutionResult("not_found",(),None,None,"no_eligible_registered_windows_device",_digest(audit))
 top=eligible[0];margin=top.confidence-(eligible[1].confidence if len(eligible)>1 else 0)
 if top.confidence>=MIN_CONFIDENCE and margin>=MIN_MARGIN:
  token=_digest({"tenant_id":tenant_id,"employee_id":employee_id,"device_id":top.device_id,"relationship_id":top.relationship_id});return ResolutionResult("pending_confirmation",(top,),top.device_id,token,"dominant_active_relationship",_digest(audit))
 return ResolutionResult("ambiguous",tuple(eligible[:MAX_DISCLOSED]),None,None,"multiple_plausible_devices",_digest(audit))
def confirm_device(result:ResolutionResult,*,tenant_id:str,employee_id:str,device_id:str,confirmation_token:str,decision:Literal["confirmed","declined"])->ResolutionResult:
 if result.outcome!="pending_confirmation" or result.selected_device_id!=device_id or result.confirmation_token!=confirmation_token:raise DeviceResolutionError("invalid confirmation context")
 expected=_digest({"tenant_id":tenant_id,"employee_id":employee_id,"device_id":device_id,"relationship_id":result.candidates[0].relationship_id})
 if confirmation_token!=expected:raise DeviceResolutionError("confirmation scope mismatch")
 outcome="confirmed" if decision=="confirmed" else "declined";return ResolutionResult(outcome,result.candidates,device_id if outcome=="confirmed" else None,None,"employee_confirmed_device" if outcome=="confirmed" else "employee_declined_device",result.provenance_sha256)
def resolution_state_update(result:ResolutionResult)->dict[str,object]:
 phase="consent" if result.outcome=="confirmed" else "clarification" if result.outcome in {"pending_confirmation","ambiguous","declined"} else "escalated"
 return {"phase":phase,"final_status":"escalated" if phase=="escalated" else None,"device_id":result.selected_device_id if result.outcome=="confirmed" else None,"device_resolution_status":result.outcome,"device_candidates":tuple({"device_id":x.device_id,"display_name":x.display_name,"operating_system":x.operating_system,"confidence":x.confidence} for x in result.candidates),"device_confirmation_token":result.confirmation_token,"device_resolution_reason":result.reason,"device_resolution_provenance_sha256":result.provenance_sha256}
