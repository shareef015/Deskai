from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

Risk = Literal["low", "medium", "high"]
Complexity = Literal["simple", "moderate", "complex"]
MAX_FALLBACKS = 2
MIN_EVALUATION_SCORE = {"low":0.90, "medium":0.95, "high":0.98}


class RoutingDenied(ValueError):
    pass


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    provider_id: str
    capabilities: frozenset[str]
    maximum_risk: Risk
    maximum_context_tokens: int
    estimated_cost_microusd: int
    p95_latency_ms: int
    evaluation_score: float
    evaluation_release_id: str
    approved: bool
    data_classes: frozenset[str]
    circuit_state: Literal["closed", "open", "half_open"]


@dataclass(frozen=True)
class RoutingRequest:
    tenant_id: str
    task_id: str
    task_type: str
    risk: Risk
    complexity: Complexity
    required_capabilities: frozenset[str]
    data_class: str
    estimated_input_tokens: int
    maximum_output_tokens: int
    latency_slo_ms: int
    remaining_token_budget: int
    remaining_cost_microusd: int
    preferred_model_id: str | None
    fallback_allowed: bool


@dataclass(frozen=True)
class RoutingDecision:
    outcome: Literal["selected", "fallback_selected", "escalate"]
    selected_model_id: str | None
    provider_id: str | None
    fallback_chain: tuple[str, ...]
    reason: str
    estimated_total_tokens: int
    estimated_cost_microusd: int
    provenance_sha256: str


def _risk_value(value: Risk) -> int:
    return {"low":0,"medium":1,"high":2}[value]


def route(request: RoutingRequest, profiles: tuple[ModelProfile, ...], governed_fallbacks: dict[str, tuple[str, ...]]) -> RoutingDecision:
    if not request.tenant_id or not request.task_id or not request.required_capabilities:
        raise RoutingDenied("routing scope or capabilities missing")
    total_tokens = request.estimated_input_tokens + request.maximum_output_tokens
    if total_tokens <= 0 or total_tokens > request.remaining_token_budget:
        raise RoutingDenied("token budget exceeded")
    if len({p.model_id for p in profiles}) != len(profiles):
        raise RoutingDenied("duplicate model profile")
    by_id = {p.model_id:p for p in profiles}
    def eligible(profile: ModelProfile) -> bool:
        return profile.approved and profile.circuit_state == "closed" and request.required_capabilities <= profile.capabilities and _risk_value(profile.maximum_risk) >= _risk_value(request.risk) and profile.maximum_context_tokens >= total_tokens and profile.estimated_cost_microusd <= request.remaining_cost_microusd and profile.p95_latency_ms <= request.latency_slo_ms and profile.evaluation_score >= MIN_EVALUATION_SCORE[request.risk] and request.data_class in profile.data_classes
    preferred = by_id.get(request.preferred_model_id) if request.preferred_model_id else None
    chain: tuple[str, ...] = ()
    outcome: Literal["selected", "fallback_selected", "escalate"] = "selected"
    selected = preferred if preferred and eligible(preferred) else None
    reason = "preferred_eligible" if selected else "quality_cost_latency_match"
    if request.preferred_model_id and not selected:
        if not request.fallback_allowed:
            return _decision(request,None,(),"escalate","preferred_unavailable_no_silent_substitution",total_tokens)
        configured = governed_fallbacks.get(request.preferred_model_id, ())
        if len(configured) > MAX_FALLBACKS:
            raise RoutingDenied("fallback hierarchy exceeds policy")
        chain = tuple(configured)
        selected = next((by_id[mid] for mid in chain if mid in by_id and eligible(by_id[mid])),None)
        outcome = "fallback_selected" if selected else "escalate"; reason = "governed_fallback" if selected else "no_governed_model_available"
    elif not selected:
        candidates = sorted((p for p in profiles if eligible(p)),key=lambda p:(p.estimated_cost_microusd,p.p95_latency_ms,-p.evaluation_score,p.model_id))
        selected = candidates[0] if candidates else None
        if not selected: outcome,reason="escalate","no_approved_model_meets_constraints"
    return _decision(request,selected,chain,outcome,reason,total_tokens)


def _decision(request: RoutingRequest, selected: ModelProfile | None, chain: tuple[str, ...], outcome: Literal["selected","fallback_selected","escalate"], reason: str, total_tokens: int) -> RoutingDecision:
    payload = {"tenant":request.tenant_id,"task":request.task_id,"risk":request.risk,"complexity":request.complexity,"required":sorted(request.required_capabilities),"data_class":request.data_class,"selected":selected.model_id if selected else None,"release":selected.evaluation_release_id if selected else None,"fallback":chain,"reason":reason,"budgets":(request.remaining_token_budget,request.remaining_cost_microusd,request.latency_slo_ms)}
    provenance=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return RoutingDecision(outcome,selected.model_id if selected else None,selected.provider_id if selected else None,chain,reason,total_tokens,selected.estimated_cost_microusd if selected else 0,provenance)
