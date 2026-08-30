from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPerformanceProfile:
    model: str
    p95_latency_ms: float
    max_concurrency: int
    input_cost_per_million: float
    output_cost_per_million: float
    quality_score: float


@dataclass(frozen=True, slots=True)
class ModelRouteBudget:
    latency_ms_max: float
    concurrency_required: int
    cost_per_request_usd_max: float
    minimum_quality: float
    estimated_input_tokens: int
    estimated_output_tokens: int


def _cost(profile: ModelPerformanceProfile, budget: ModelRouteBudget) -> float:
    return (
        budget.estimated_input_tokens / 1_000_000 * profile.input_cost_per_million
        + budget.estimated_output_tokens / 1_000_000 * profile.output_cost_per_million
    )


def eligible_models(
    profiles: tuple[ModelPerformanceProfile, ...], budget: ModelRouteBudget
) -> tuple[ModelPerformanceProfile, ...]:
    eligible = [
        profile
        for profile in profiles
        if profile.p95_latency_ms <= budget.latency_ms_max
        and profile.max_concurrency >= budget.concurrency_required
        and profile.quality_score >= budget.minimum_quality
        and _cost(profile, budget) <= budget.cost_per_request_usd_max
    ]
    return tuple(sorted(eligible, key=lambda profile: (-profile.quality_score, profile.p95_latency_ms, profile.model)))
