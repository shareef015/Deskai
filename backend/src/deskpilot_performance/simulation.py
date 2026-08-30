from __future__ import annotations

from .fairness import jain_fairness_index
from .models import CapacityEnvelope, ResourceSnapshot, ScenarioResult, StageBudget
from .stats import summarize_stage


DEFAULT_STAGE_BUDGETS = (
    StageBudget("api", 250, 500, 0.005),
    StageBudget("rag", 700, 1200, 0.01),
    StageBudget("langgraph", 300, 650, 0.005),
    StageBudget("llm", 2500, 4500, 0.02),
    StageBudget("mcp", 800, 1500, 0.01),
    StageBudget("stream_publish", 120, 250, 0.005),
    StageBudget("end_to_end", 4200, 6500, 0.02),
)

DEFAULT_ENVELOPE = CapacityEnvelope(
    api_rps=120.0,
    concurrent_incidents=250,
    sse_connections=2_000,
    websocket_connections=1_000,
    rag_qps=60.0,
    agent_concurrency=80,
    mcp_concurrency=40,
)


def _samples(base: float, count: int = 100) -> list[float]:
    # Deterministic spread with bounded tails; suitable for regression tests, not real capacity claims.
    pattern = (0.72, 0.78, 0.82, 0.86, 0.90, 0.94, 0.98, 1.00, 1.04, 1.08, 1.12, 1.18)
    return [base * pattern[index % len(pattern)] for index in range(count)]


def synthetic_baseline() -> ScenarioResult:
    stages = (
        summarize_stage("api", _samples(145)),
        summarize_stage("rag", _samples(410)),
        summarize_stage("langgraph", _samples(170)),
        summarize_stage("llm", _samples(1450)),
        summarize_stage("mcp", _samples(460)),
        summarize_stage("stream_publish", _samples(65)),
        summarize_stage("end_to_end", _samples(2850)),
    )
    resources = ResourceSnapshot(0.62, 0.58, 0.61, 0.55, 0.64, 12)
    return ScenarioResult(
        "performance-synthetic-baseline",
        stages,
        resources,
        achieved_rps=120.0,
        target_rps=120.0,
        tenant_fairness_index=jain_fairness_index([100, 99, 101, 100]),
        cache_hit_ratio=0.68,
        queue_oldest_age_seconds=2.5,
    )


def synthetic_regression() -> ScenarioResult:
    stages = (
        summarize_stage("api", _samples(300)),
        summarize_stage("rag", _samples(900)),
        summarize_stage("langgraph", _samples(170)),
        summarize_stage("llm", _samples(2200)),
        summarize_stage("mcp", _samples(950)),
        summarize_stage("stream_publish", _samples(65)),
        summarize_stage("end_to_end", _samples(4700)),
    )
    resources = ResourceSnapshot(0.94, 0.88, 0.91, 0.84, 0.93, 1200)
    return ScenarioResult(
        "performance-synthetic-regression",
        stages,
        resources,
        achieved_rps=88.0,
        target_rps=120.0,
        tenant_fairness_index=jain_fairness_index([180, 20, 15, 10]),
        cache_hit_ratio=0.15,
        queue_oldest_age_seconds=75.0,
        dropped_requests=27,
    )
