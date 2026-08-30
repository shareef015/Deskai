from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import ResourceSnapshot


class DegradationMode(StrEnum):
    NORMAL = "normal"
    SHED_OPTIONAL = "shed_optional"
    READ_ONLY = "read_only"
    PROTECTIVE = "protective"


@dataclass(frozen=True, slots=True)
class DegradationDecision:
    mode: DegradationMode
    allow_new_ai_runs: bool
    allow_remediation: bool
    allow_optional_enrichment: bool
    reason: str


def decide_degradation(resources: ResourceSnapshot, *, queue_oldest_age_seconds: float) -> DegradationDecision:
    peak = max(
        resources.cpu_utilization,
        resources.memory_utilization,
        resources.postgres_pool_utilization,
        resources.redis_pool_utilization,
        resources.mcp_worker_utilization,
    )
    if peak >= 0.98 or queue_oldest_age_seconds >= 120:
        return DegradationDecision(DegradationMode.PROTECTIVE, False, False, False, "critical_capacity_pressure")
    if peak >= 0.92 or queue_oldest_age_seconds >= 60:
        return DegradationDecision(DegradationMode.READ_ONLY, True, False, False, "high_capacity_pressure")
    if peak >= 0.80 or queue_oldest_age_seconds >= 20:
        return DegradationDecision(DegradationMode.SHED_OPTIONAL, True, True, False, "elevated_capacity_pressure")
    return DegradationDecision(DegradationMode.NORMAL, True, True, True, "within_capacity_envelope")
