from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StageBudget:
    name: str
    p95_ms_max: float
    p99_ms_max: float
    error_rate_max: float = 0.01

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("stage name is required")
        if self.p95_ms_max <= 0 or self.p99_ms_max <= 0:
            raise ValueError("latency budgets must be positive")
        if self.p99_ms_max < self.p95_ms_max:
            raise ValueError("p99 budget must be >= p95 budget")
        if not 0 <= self.error_rate_max <= 1:
            raise ValueError("error_rate_max must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class StageSummary:
    name: str
    count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    error_rate: float


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    cpu_utilization: float
    memory_utilization: float
    postgres_pool_utilization: float
    redis_pool_utilization: float
    mcp_worker_utilization: float
    queue_depth: int

    def __post_init__(self) -> None:
        for value in (
            self.cpu_utilization,
            self.memory_utilization,
            self.postgres_pool_utilization,
            self.redis_pool_utilization,
            self.mcp_worker_utilization,
        ):
            if not 0 <= value <= 1:
                raise ValueError("resource utilization must be between 0 and 1")
        if self.queue_depth < 0:
            raise ValueError("queue_depth cannot be negative")


@dataclass(frozen=True, slots=True)
class CapacityEnvelope:
    api_rps: float
    concurrent_incidents: int
    sse_connections: int
    websocket_connections: int
    rag_qps: float
    agent_concurrency: int
    mcp_concurrency: int

    def __post_init__(self) -> None:
        if min(self.api_rps, self.rag_qps) < 0:
            raise ValueError("rates cannot be negative")
        if min(
            self.concurrent_incidents,
            self.sse_connections,
            self.websocket_connections,
            self.agent_concurrency,
            self.mcp_concurrency,
        ) < 0:
            raise ValueError("capacities cannot be negative")


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    name: str
    stage_summaries: tuple[StageSummary, ...]
    resources: ResourceSnapshot
    achieved_rps: float
    target_rps: float
    tenant_fairness_index: float
    cache_hit_ratio: float
    queue_oldest_age_seconds: float
    dropped_requests: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("scenario name required")
        if min(self.achieved_rps, self.target_rps, self.queue_oldest_age_seconds) < 0:
            raise ValueError("rates/ages cannot be negative")
        if not 0 <= self.tenant_fairness_index <= 1:
            raise ValueError("fairness must be between 0 and 1")
        if not 0 <= self.cache_hit_ratio <= 1:
            raise ValueError("cache hit ratio must be between 0 and 1")
        if self.dropped_requests < 0:
            raise ValueError("dropped_requests cannot be negative")


@dataclass(frozen=True, slots=True)
class PerformanceCertificate:
    passed: bool
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    fingerprint: str
    envelope: CapacityEnvelope
