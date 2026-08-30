from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

MAX_PLAN_STEPS = 8
MAX_REPLANS = 2
MAX_TOOL_CALLS = 12
MAX_PLAN_TOKENS = 4000
MAX_PLAN_DURATION_SECONDS = 600
FORBIDDEN_GOALS = frozenset({"bypass_consent","bypass_approval","disable_security","collect_credentials","hide_evidence","claim_unverified_resolution","expand_tenant_scope","arbitrary_command_execution"})


class PlanDenied(ValueError):
    pass


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    objective: str
    dependencies: tuple[str,...]
    required_evidence_ids: tuple[str,...]
    tool_id: str | None
    risk: Literal["read_only","low","medium","high"]
    expected_output: str


@dataclass(frozen=True)
class ProposedPlan:
    tenant_id: str
    incident_id: str
    objective_id: str
    version: int
    parent_plan_sha256: str | None
    replan_count: int
    estimated_tokens: int
    estimated_tool_calls: int
    estimated_duration_seconds: int
    steps: tuple[PlanStep,...]


@dataclass(frozen=True)
class ValidatedPlan:
    outcome: Literal["critic_review","escalate"]
    ordered_step_ids: tuple[str,...]
    maximum_risk: str
    plan_sha256: str
    reason: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def _topological(steps: tuple[PlanStep,...]) -> tuple[str,...]:
    by_id={s.step_id:s for s in steps}
    if len(by_id)!=len(steps) or any(not s.step_id for s in steps): raise PlanDenied("duplicate or empty step ID")
    if any(dep not in by_id or dep==s.step_id for s in steps for dep in s.dependencies): raise PlanDenied("invalid dependency")
    result=[];remaining=set(by_id)
    while remaining:
        ready=sorted(sid for sid in remaining if set(by_id[sid].dependencies)<=set(result))
        if not ready: raise PlanDenied("cyclic plan")
        result.extend(ready);remaining-=set(ready)
    return tuple(result)


def validate_plan(plan: ProposedPlan, *, approved_objectives: frozenset[str], allowed_tools: frozenset[str], available_evidence_ids: frozenset[str]) -> ValidatedPlan:
    if not plan.tenant_id or not plan.incident_id or plan.objective_id not in approved_objectives or plan.objective_id in FORBIDDEN_GOALS: raise PlanDenied("objective not approved")
    if not plan.steps or len(plan.steps)>MAX_PLAN_STEPS or plan.replan_count<0 or plan.replan_count>MAX_REPLANS: raise PlanDenied("plan or replan limit exceeded")
    if plan.estimated_tokens>MAX_PLAN_TOKENS or plan.estimated_tool_calls>MAX_TOOL_CALLS or plan.estimated_duration_seconds>MAX_PLAN_DURATION_SECONDS: raise PlanDenied("plan budget exceeded")
    if plan.version!=plan.replan_count+1 or (plan.replan_count>0 and (not plan.parent_plan_sha256 or len(plan.parent_plan_sha256)!=64)): raise PlanDenied("immutable replan lineage required")
    ordered=_topological(plan.steps)
    for step in plan.steps:
        if step.objective in FORBIDDEN_GOALS: raise PlanDenied("forbidden step objective")
        if step.tool_id and step.tool_id not in allowed_tools: raise PlanDenied("tool outside plan allowlist")
        if step.risk!="read_only" and not step.required_evidence_ids: raise PlanDenied("state-changing or risky step requires evidence")
        if not set(step.required_evidence_ids)<=available_evidence_ids: raise PlanDenied("step references unavailable evidence")
        if not step.expected_output: raise PlanDenied("step output contract missing")
    tool_count=sum(step.tool_id is not None for step in plan.steps)
    if tool_count>plan.estimated_tool_calls: raise PlanDenied("declared tool budget understates plan")
    maximum=max((s.risk for s in plan.steps),key={"read_only":0,"low":1,"medium":2,"high":3}.__getitem__)
    payload={"tenant":plan.tenant_id,"incident":plan.incident_id,"objective":plan.objective_id,"version":plan.version,"parent":plan.parent_plan_sha256,"replans":plan.replan_count,"budgets":(plan.estimated_tokens,plan.estimated_tool_calls,plan.estimated_duration_seconds),"steps":[s.__dict__ for s in plan.steps],"ordered":ordered}
    return ValidatedPlan("critic_review",ordered,maximum,_digest(payload),"bounded_plan_requires_independent_critic")


def accept_critic_review(validated: ValidatedPlan, *, critic_status: str, reviewed_plan_sha256: str) -> dict[str,object]:
    if critic_status!="pass" or reviewed_plan_sha256!=validated.plan_sha256: raise PlanDenied("exact plan critic pass required")
    return {"planning_status":"approved_for_orchestration","planning_plan_sha256":validated.plan_sha256,"planning_ordered_step_ids":validated.ordered_step_ids,"planning_maximum_risk":validated.maximum_risk}
