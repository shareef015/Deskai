from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .degradation import DegradationMode, decide_degradation
from .models import CapacityEnvelope, PerformanceCertificate, ScenarioResult, StageBudget


@dataclass(frozen=True, slots=True)
class PerformanceThresholds:
    minimum_throughput_ratio: float = 0.98
    minimum_tenant_fairness: float = 0.95
    minimum_cache_hit_ratio: float = 0.50
    maximum_queue_oldest_age_seconds: float = 30.0
    maximum_cpu_utilization: float = 0.85
    maximum_memory_utilization: float = 0.85
    maximum_postgres_pool_utilization: float = 0.80
    maximum_redis_pool_utilization: float = 0.80
    maximum_mcp_worker_utilization: float = 0.85
    maximum_dropped_requests: int = 0


class PerformanceGate:
    def __init__(
        self,
        stage_budgets: tuple[StageBudget, ...],
        *,
        thresholds: PerformanceThresholds | None = None,
    ) -> None:
        if not stage_budgets:
            raise ValueError("at least one stage budget is required")
        self.stage_budgets = {budget.name: budget for budget in stage_budgets}
        self.thresholds = thresholds or PerformanceThresholds()

    def certify(self, scenario: ScenarioResult, envelope: CapacityEnvelope) -> PerformanceCertificate:
        t = self.thresholds
        failures: list[str] = []
        warnings: list[str] = []
        summaries = {summary.name: summary for summary in scenario.stage_summaries}
        for name, budget in self.stage_budgets.items():
            summary = summaries.get(name)
            if summary is None:
                failures.append(f"missing_stage:{name}")
                continue
            if summary.p95_ms > budget.p95_ms_max:
                failures.append(f"p95:{name}")
            if summary.p99_ms > budget.p99_ms_max:
                failures.append(f"p99:{name}")
            if summary.error_rate > budget.error_rate_max:
                failures.append(f"error_rate:{name}")

        throughput_ratio = 1.0 if scenario.target_rps == 0 else scenario.achieved_rps / scenario.target_rps
        if throughput_ratio < t.minimum_throughput_ratio:
            failures.append("throughput")
        if scenario.tenant_fairness_index < t.minimum_tenant_fairness:
            failures.append("tenant_fairness")
        if scenario.cache_hit_ratio < t.minimum_cache_hit_ratio:
            warnings.append("cache_hit_ratio")
        if scenario.queue_oldest_age_seconds > t.maximum_queue_oldest_age_seconds:
            failures.append("queue_age")
        if scenario.dropped_requests > t.maximum_dropped_requests:
            failures.append("dropped_requests")

        resource_checks = {
            "cpu": (scenario.resources.cpu_utilization, t.maximum_cpu_utilization),
            "memory": (scenario.resources.memory_utilization, t.maximum_memory_utilization),
            "postgres_pool": (scenario.resources.postgres_pool_utilization, t.maximum_postgres_pool_utilization),
            "redis_pool": (scenario.resources.redis_pool_utilization, t.maximum_redis_pool_utilization),
            "mcp_workers": (scenario.resources.mcp_worker_utilization, t.maximum_mcp_worker_utilization),
        }
        for name, (actual, limit) in resource_checks.items():
            if actual > limit:
                failures.append(f"resource:{name}")

        degradation = decide_degradation(scenario.resources, queue_oldest_age_seconds=scenario.queue_oldest_age_seconds)
        if degradation.mode is not DegradationMode.NORMAL:
            warnings.append(f"degradation:{degradation.mode}")

        unique_failures = tuple(sorted(set(failures)))
        unique_warnings = tuple(sorted(set(warnings)))
        payload = {
            "scenario": asdict(scenario),
            "envelope": asdict(envelope),
            "failures": unique_failures,
            "warnings": unique_warnings,
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return PerformanceCertificate(not unique_failures, unique_failures, unique_warnings, fingerprint, envelope)
