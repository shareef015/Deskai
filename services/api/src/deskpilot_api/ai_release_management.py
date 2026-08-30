from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from typing import Literal
class ReleaseDenied(ValueError):pass
@dataclass(frozen=True)
class Actor:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Bundle:
 bundle_id:str;tenant_id:str;author_id:str;prompt_version:str;agent_version:str;model_profile_version:str;graph_version:str;schema_version:str;evaluation_run_sha256:str;compatibility:dict[str,bool];bundle_sha256:str
@dataclass(frozen=True)
class DeploymentEvent:event_id:str;event_type:str;actor_sha256:str;bundle_id:str;environment:str;canary_percent:int;prior_bundle_id:str|None;event_sha256:str
@dataclass
class Deployment:
 tenant_id:str;environment:Literal["synthetic","staging","production"];active_bundle_id:str|None=None;canary_bundle_id:str|None=None;canary_percent:int=0;frozen:bool=False;events:list[DeploymentEvent]=field(default_factory=list)
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
class ReleaseStore:
 def __init__(self)->None:self.bundles:dict[str,Bundle]={};self.approved:set[str]=set();self.deployments:dict[tuple[str,str],Deployment]={}
 def register(self,actor:Actor,bundle:Bundle)->Bundle:
  self._scope(actor,bundle.tenant_id)
  if actor.subject!=bundle.author_id or "release_author" not in actor.roles:raise ReleaseDenied("author denied")
  if bundle.bundle_id in self.bundles or bundle.bundle_sha256!=_digest({**bundle.__dict__,"bundle_sha256":""}):raise ReleaseDenied("immutable bundle conflict")
  if not bundle.compatibility or not all(bundle.compatibility.values()) or len(bundle.evaluation_run_sha256)!=64:raise ReleaseDenied("compatibility or evaluation gate failed")
  self.bundles[bundle.bundle_id]=bundle;return bundle
 def approve(self,actor:Actor,bundle_id:str)->None:
  bundle=self._bundle(actor,bundle_id)
  if actor.subject==bundle.author_id or "release_approver" not in actor.roles:raise ReleaseDenied("independent approval required")
  self.approved.add(bundle_id)
 def rollout(self,actor:Actor,bundle_id:str,environment:str,canary_percent:int)->Deployment:
  bundle=self._bundle(actor,bundle_id)
  if bundle_id not in self.approved or "release_manager" not in actor.roles:raise ReleaseDenied("approved release manager required")
  if environment not in {"synthetic","staging","production"} or not 0<canary_percent<=100:raise ReleaseDenied("invalid rollout")
  key=(bundle.tenant_id,environment);deployment=self.deployments.setdefault(key,Deployment(bundle.tenant_id,environment))
  if deployment.frozen:raise ReleaseDenied("deployment frozen")
  prior=deployment.active_bundle_id;deployment.canary_bundle_id=bundle_id;deployment.canary_percent=canary_percent
  if canary_percent==100:deployment.active_bundle_id=bundle_id;deployment.canary_bundle_id=None;deployment.canary_percent=0
  self._event(deployment,"rollout",actor,bundle_id,canary_percent,prior);return deployment
 def rollback(self,actor:Actor,tenant_id:str,environment:str,target_bundle_id:str)->Deployment:
  self._scope(actor,tenant_id);deployment=self.deployments.get((tenant_id,environment))
  if not deployment or target_bundle_id not in self.approved or "release_manager" not in actor.roles:raise ReleaseDenied("rollback denied")
  prior=deployment.active_bundle_id;deployment.active_bundle_id=target_bundle_id;deployment.canary_bundle_id=None;deployment.canary_percent=0;self._event(deployment,"rollback",actor,target_bundle_id,100,prior);return deployment
 def freeze(self,actor:Actor,tenant_id:str,environment:str)->Deployment:
  self._scope(actor,tenant_id)
  if "emergency_controller" not in actor.roles:raise ReleaseDenied("freeze denied")
  deployment=self.deployments.setdefault((tenant_id,environment),Deployment(tenant_id,environment));deployment.frozen=True;self._event(deployment,"freeze",actor,deployment.active_bundle_id or "none",0,deployment.active_bundle_id);return deployment
 def _bundle(self,actor:Actor,bundle_id:str)->Bundle:
  bundle=self.bundles.get(bundle_id)
  if not bundle:raise ReleaseDenied("bundle not found")
  self._scope(actor,bundle.tenant_id);return bundle
 def _event(self,deployment:Deployment,event_type:str,actor:Actor,bundle_id:str,percent:int,prior:str|None)->None:
  payload=(deployment.tenant_id,deployment.environment,len(deployment.events),event_type,bundle_id,percent,prior);digest=_digest(payload);deployment.events.append(DeploymentEvent(digest,event_type,_digest(actor.subject),bundle_id,deployment.environment,percent,prior,digest))
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise ReleaseDenied("authenticated tenant scope required")
