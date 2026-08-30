from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from redis.asyncio import Redis


class SessionCodec:
    def __init__(self, keys: Mapping[str, bytes], active_version: str) -> None:
        if active_version not in keys or any(len(key) != 32 for key in keys.values()):
            raise ValueError("session keys must be versioned AES-256 keys")
        self._keys = dict(keys)
        self._active = active_version

    def encrypt(self, session_id: str, payload: Mapping[str, Any]) -> bytes:
        nonce = os.urandom(12)
        plaintext = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        ciphertext = AESGCM(self._keys[self._active]).encrypt(
            nonce, plaintext, session_id.encode()
        )
        return self._active.encode() + b"." + nonce + ciphertext

    def decrypt(self, session_id: str, envelope: bytes) -> dict[str, Any]:
        version_raw, body = envelope.split(b".", 1)
        version = version_raw.decode()
        key = self._keys.get(version)
        if key is None or len(body) < 13:
            raise ValueError("session envelope rejected")
        plaintext = AESGCM(key).decrypt(body[:12], body[12:], session_id.encode())
        value = json.loads(plaintext)
        if not isinstance(value, dict):
            raise ValueError("session payload rejected")
        return value


class EncryptedSessionStore:
    def __init__(self, redis: Redis, codec: SessionCodec, *, idle_ttl_seconds: int = 1800) -> None:
        self._redis = redis
        self._codec = codec
        self._ttl = idle_ttl_seconds

    async def save(self, key: str, session_id: str, payload: Mapping[str, Any]) -> None:
        await self._redis.set(key, self._codec.encrypt(session_id, payload), ex=self._ttl)

    async def load(self, key: str, session_id: str) -> dict[str, Any] | None:
        envelope = await self._redis.getex(key, ex=self._ttl)
        return None if envelope is None else self._codec.decrypt(session_id, envelope)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)
