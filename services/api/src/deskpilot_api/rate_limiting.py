from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request, Response
from redis.asyncio import Redis

from deskpilot_core.errors import DeskPilotError, ErrorCode
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from deskpilot_api.auth.dependencies import require_principal

_MULTI_BUCKET = """
local now_parts = redis.call('TIME')
local now = tonumber(now_parts[1]) + tonumber(now_parts[2]) / 1000000
local computed = {}
local retry_after = 0
for i, key in ipairs(KEYS) do
  local offset = (i - 1) * 3
  local capacity = tonumber(ARGV[offset + 1])
  local refill = tonumber(ARGV[offset + 2])
  local cost = tonumber(ARGV[offset + 3])
  local values = redis.call('HMGET', key, 'tokens', 'updated')
  local tokens = tonumber(values[1]) or capacity
  local updated = tonumber(values[2]) or now
  tokens = math.min(capacity, tokens + math.max(0, now - updated) * refill)
  computed[i] = {tokens, capacity, refill, cost}
  if tokens < cost then
    retry_after = math.max(retry_after, math.ceil((cost - tokens) / refill))
  end
end
if retry_after > 0 then return {0, 0, retry_after} end
local minimum_remaining = nil
for i, key in ipairs(KEYS) do
  local item = computed[i]
  local remaining = item[1] - item[4]
  redis.call('HSET', key, 'tokens', remaining, 'updated', now)
  redis.call('EXPIRE', key, math.ceil(item[2] / item[3] * 2))
  if minimum_remaining == nil or remaining < minimum_remaining then minimum_remaining = remaining end
end
return {1, math.floor(minimum_remaining), 0}
"""


@dataclass(frozen=True, slots=True)
class Bucket:
    key: str
    capacity: int
    refill_per_second: float


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class DistributedRateLimiter:
    def __init__(self, redis: Redis, namespace_key: bytes) -> None:
        self._redis = redis
        self._namespace_key = namespace_key

    def pseudonym(self, value: str) -> str:
        return hmac.new(self._namespace_key, value.encode(), hashlib.sha256).hexdigest()[:32]

    async def consume(self, buckets: tuple[Bucket, ...], cost: int) -> RateLimitDecision:
        if not buckets or cost < 1: raise ValueError("rate-limit buckets and positive cost required")
        arguments: list[float | int] = []
        for bucket in buckets: arguments.extend((bucket.capacity, bucket.refill_per_second, cost))
        result = await self._redis.eval(_MULTI_BUCKET, len(buckets), *(bucket.key for bucket in buckets), *arguments)
        allowed, remaining, retry_after = (int(value) for value in result)
        return RateLimitDecision(bool(allowed), min(item.capacity for item in buckets), remaining, retry_after)


def _request_cost(request: Request) -> int:
    path = request.url.path
    if path.endswith("/events/stream"): return 2
    if path.endswith("/transitions"): return 5
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}: return 2
    return 1


async def enforce_rate_limit(
    request: Request,
    response: Response,
    principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)],
) -> RateLimitDecision:
    limiter = getattr(request.app.state, "rate_limiter", None)
    if not isinstance(limiter, DistributedRateLimiter):
        raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30)
    tenant = limiter.pseudonym(str(principal.tenant_id))
    subject = limiter.pseudonym(principal.subject)
    network = limiter.pseudonym(request.client.host if request.client else "unknown")
    buckets = (
        Bucket(f"deskpilot:v1:rate:tenant:{tenant}", 600, 10),
        Bucket(f"deskpilot:v1:rate:user:{tenant}:{subject}", 120, 2),
        Bucket(f"deskpilot:v1:rate:network:{network}", 180, 3),
    )
    try:
        decision = await limiter.consume(buckets, _request_cost(request))
    except Exception as exc:
        raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30) from exc
    response.headers["RateLimit-Limit"] = str(decision.limit)
    response.headers["RateLimit-Remaining"] = str(max(decision.remaining, 0))
    response.headers["RateLimit-Reset"] = str(decision.retry_after_seconds)
    if not decision.allowed:
        raise DeskPilotError(ErrorCode.RATE_LIMITED, retry_after_seconds=max(decision.retry_after_seconds, 1))
    return decision
