from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int


@dataclass(slots=True)
class _Bucket:
    tokens: float
    updated_at: float


class TokenBucketLimiter:
    """Deterministic reference token bucket. Use Redis/edge storage for distributed production enforcement."""

    def __init__(self, *, capacity: int, refill_per_second: float) -> None:
        if capacity <= 0 or refill_per_second <= 0:
            raise ValueError("invalid_rate_limit")
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._buckets: dict[str, _Bucket] = {}

    def check(self, key: str, *, cost: int = 1, now: float | None = None) -> RateLimitDecision:
        if cost <= 0 or cost > self.capacity:
            raise ValueError("invalid_cost")
        current = time.time() if now is None else now
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(float(self.capacity), current)
            self._buckets[key] = bucket
        elapsed = max(0.0, current - bucket.updated_at)
        bucket.tokens = min(float(self.capacity), bucket.tokens + elapsed * self.refill_per_second)
        bucket.updated_at = current
        if bucket.tokens >= cost:
            bucket.tokens -= cost
            return RateLimitDecision(True, int(bucket.tokens), 0)
        deficit = cost - bucket.tokens
        retry_after = max(1, int(deficit / self.refill_per_second + 0.999999))
        return RateLimitDecision(False, int(bucket.tokens), retry_after)
