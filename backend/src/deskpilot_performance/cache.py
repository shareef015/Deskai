from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CacheEfficiency:
    requests: int
    hits: int
    hit_ratio: float
    avoided_compute_ms: float
    avoided_cost_usd: float


def evaluate_cache(
    *, requests: int, hits: int, compute_ms_per_miss: float, cost_usd_per_miss: float
) -> CacheEfficiency:
    if requests < 0 or hits < 0 or hits > requests:
        raise ValueError("invalid request/hit counts")
    if compute_ms_per_miss < 0 or cost_usd_per_miss < 0:
        raise ValueError("compute/cost must be non-negative")
    ratio = 0.0 if requests == 0 else hits / requests
    return CacheEfficiency(requests, hits, ratio, hits * compute_ms_per_miss, hits * cost_usd_per_miss)
