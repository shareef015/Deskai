from __future__ import annotations

import secrets

from redis.asyncio import Redis


_RELEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""


class DistributedLock:
    def __init__(self, redis: Redis, key: str, *, ttl_ms: int) -> None:
        if not 1000 <= ttl_ms <= 120_000:
            raise ValueError("lock TTL must be between 1 and 120 seconds")
        self._redis = redis
        self._key = key
        self._ttl_ms = ttl_ms
        self._token = secrets.token_urlsafe(32)
        self.acquired = False

    async def acquire(self) -> bool:
        self.acquired = bool(
            await self._redis.set(self._key, self._token, nx=True, px=self._ttl_ms)
        )
        return self.acquired

    async def release(self) -> bool:
        if not self.acquired:
            return False
        deleted = await self._redis.eval(_RELEASE, 1, self._key, self._token)
        self.acquired = False
        return bool(deleted)

    async def __aenter__(self) -> DistributedLock:
        if not await self.acquire():
            raise RuntimeError("distributed lock is already held")
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.release()
