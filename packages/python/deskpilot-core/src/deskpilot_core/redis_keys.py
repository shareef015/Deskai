from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from uuid import UUID


_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


@dataclass(frozen=True, slots=True)
class RedisKeyspace:
    namespace_key: bytes
    prefix: str = "deskpilot:v1"

    def tenant_namespace(self, tenant_id: UUID) -> str:
        return hmac.new(self.namespace_key, tenant_id.bytes, hashlib.sha256).hexdigest()[:32]

    def key(self, tenant_id: UUID, domain: str, identifier: str, *parts: str) -> str:
        segments = (domain, identifier, *parts)
        if not all(_SEGMENT.fullmatch(segment) for segment in segments):
            raise ValueError("invalid Redis key segment")
        value = ":".join((self.prefix, self.tenant_namespace(tenant_id), *segments))
        if len(value) > 240:
            raise ValueError("Redis key exceeds maximum length")
        return value

    def opaque_identifier(self, value: str) -> str:
        return hmac.new(self.namespace_key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
