from __future__ import annotations

from math import ceil

from .models import StageSummary


def percentile(values: list[float] | tuple[float, ...], percentile_value: float) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    if not 0 <= percentile_value <= 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(float(v) for v in values)
    rank = max(1, ceil((percentile_value / 100) * len(ordered)))
    return ordered[rank - 1]


def summarize_stage(name: str, latencies_ms: list[float], *, errors: int = 0) -> StageSummary:
    if not latencies_ms:
        raise ValueError("latencies cannot be empty")
    if errors < 0 or errors > len(latencies_ms):
        raise ValueError("errors must be within sample count")
    return StageSummary(
        name=name,
        count=len(latencies_ms),
        p50_ms=percentile(latencies_ms, 50),
        p95_ms=percentile(latencies_ms, 95),
        p99_ms=percentile(latencies_ms, 99),
        max_ms=max(latencies_ms),
        error_rate=errors / len(latencies_ms),
    )
