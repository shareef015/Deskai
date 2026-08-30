from __future__ import annotations
import hashlib,json
from dataclasses import dataclass,field
from datetime import datetime,timezone
from typing import Literal
TERMINAL=frozenset({"approved","rejected","expired","superseded"})
class ReviewDenied(ValueError):pass
@dataclass(frozen=True)
class Reviewer:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Action:action_id:str;capability:str;risk:Literal["low","medium","high"];depends_on:tuple[str,...];before:dict[str,object];after:dict[str,object];rollback_capability:str|None;verification_id:str
@dataclass(frozen=True)
class Plan:plan_id:str;tenant_id:str;incident_id:str;checkpoint_id:str;requester_id:str;created_at:str;expires_at:str;actions:tuple[Action,...];evidence_ids:tuple[str,...];plan_sha256:str
@dataclass(frozen=True)
class Decision:decision_id:str;plan_id:str;tenant_id:str;actor_id:str;outcome:Literal["approved","rejected"];reason_code:str;expected_checkpoint_id:str;expected_plan_sha256:str;decided_at:str
@dataclass
class Review:plan:Plan;status:str="pending";decision:Decision|None=None;processed:dict[str,str]=field(default_factory=dict)
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=lambda item:item.__dict__ if hasattr(item,"__dict__") else list(item)).encode()).hexdigest()
def _time(value:str)->datetime:
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
 except ValueError as exc:raise ReviewDenied("invalid timestamp") from exc
class ReviewStore:
 def __init__(self)->None:self.rows:dict[str,Review]={}
 def submit(self,actor:Reviewer,plan:Plan)->Review:
  self._scope(actor,plan.tenant_id)
  if actor.subject!=plan.requester_id or not actor.roles.intersection({"service_desk_engineer","operator"}):raise ReviewDenied("authorized requester required")
  if plan.plan_id in self.rows:raise ReviewDenied("immutable plan already exists")
  if _time(plan.expires_at)<=_time(plan.created_at):raise ReviewDenied("invalid expiry")
  if plan.plan_sha256!=_digest({**plan.__dict__,"plan_sha256":""}):raise ReviewDenied("plan digest mismatch")
  self._validate_actions(plan.actions);review=Review(plan);self.rows[plan.plan_id]=review;return review
 def decide(self,actor:Reviewer,decision:Decision)->dict[str,object]:
  self._scope(actor,decision.tenant_id);review=self.rows.get(decision.plan_id)
  if not review or review.plan.tenant_id!=decision.tenant_id:raise ReviewDenied("plan not found")
  fingerprint=_digest(decision.__dict__)
  if decision.decision_id in review.processed:
   if review.processed[decision.decision_id]!=fingerprint:raise ReviewDenied("idempotency conflict")
   return self._view(review,True)
  if review.status in TERMINAL:raise ReviewDenied("review terminal")
  plan=review.plan
  if actor.subject!=decision.actor_id or not actor.roles.intersection({"approver","change_manager"}):raise ReviewDenied("approver authority denied")
  if actor.subject==plan.requester_id:raise ReviewDenied("self approval denied")
  if decision.expected_checkpoint_id!=plan.checkpoint_id or decision.expected_plan_sha256!=plan.plan_sha256:raise ReviewDenied("review concurrency mismatch")
  if _time(decision.decided_at)>=_time(plan.expires_at):review.status="expired";raise ReviewDenied("review expired")
  if decision.outcome=="rejected" and not decision.reason_code:raise ReviewDenied("rejection reason required")
  review.status=decision.outcome;review.decision=decision;review.processed[decision.decision_id]=fingerprint;return self._view(review,False)
 def execution_route(self,plan_id:str,outcomes:dict[str,str])->Literal["verify","rollback","human_recovery"]:
  review=self.rows.get(plan_id)
  if not review or review.status!="approved":raise ReviewDenied("approved plan required")
  if set(outcomes)!=set(action.action_id for action in review.plan.actions):raise ReviewDenied("complete action results required")
  if all(value=="succeeded" for value in outcomes.values()):return "verify"
  failed=[action for action in review.plan.actions if outcomes[action.action_id]!="succeeded"]
  return "rollback" if all(action.rollback_capability for action in failed) else "human_recovery"
 def _validate_actions(self,actions:tuple[Action,...])->None:
  if not actions:raise ReviewDenied("plan actions required")
  ids=[action.action_id for action in actions]
  if len(ids)!=len(set(ids)):raise ReviewDenied("duplicate action id")
  known=set(ids)
  for action in actions:
   if not set(action.depends_on)<known or action.action_id in action.depends_on:raise ReviewDenied("invalid dependency")
   if action.risk in {"medium","high"} and not action.rollback_capability:raise ReviewDenied("rollback required")
  visited:set[str]=set()
  def visit(node:str,path:set[str])->None:
   if node in path:raise ReviewDenied("cyclic dependency")
   if node in visited:return
   path.add(node)
   for dep in next(action for action in actions if action.action_id==node).depends_on:visit(dep,path)
   path.remove(node);visited.add(node)
  for node in ids:visit(node,set())
 def _scope(self,actor:Reviewer,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise ReviewDenied("authenticated tenant scope required")
 def _view(self,review:Review,idempotent:bool)->dict[str,object]:return {"plan_id":review.plan.plan_id,"status":review.status,"plan_sha256":review.plan.plan_sha256,"idempotent_replay":idempotent}
