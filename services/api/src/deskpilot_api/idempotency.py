from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{16,128}$")


def request_fingerprint(method: str, route: str, body: Mapping[str, Any], preconditions: Mapping[str, Any]) -> str:
    canonical = json.dumps({"method": method.upper(), "route": route, "body": body, "preconditions": preconditions}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Reservation:
    state: str
    owner_token: str | None = None
    response_status: int | None = None
    response_headers: Mapping[str, str] | None = None
    response_body: Mapping[str, Any] | None = None


class IdempotencyCodec:
    def __init__(self, key: bytes) -> None:
        if len(key) != 32: raise ValueError("idempotency encryption key must be 32 bytes")
        self._aead = AESGCM(key)

    def encrypt(self, associated_data: str, body: Mapping[str, Any]) -> bytes:
        nonce = secrets.token_bytes(12)
        plaintext = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()
        return nonce + self._aead.encrypt(nonce, plaintext, associated_data.encode())

    def decrypt(self, associated_data: str, envelope: bytes) -> Mapping[str, Any]:
        return json.loads(self._aead.decrypt(envelope[:12], envelope[12:], associated_data.encode()))


class IdempotencyStore:
    def __init__(self, session: AsyncSession, tenant_id: UUID, codec: IdempotencyCodec) -> None:
        self._session, self._tenant_id, self._codec = session, tenant_id, codec

    async def reserve(self, key: str, operation: str, fingerprint: str) -> Reservation:
        if not KEY_PATTERN.fullmatch(key): raise ValueError("invalid idempotency key")
        now, owner = datetime.now(UTC), secrets.token_urlsafe(32)
        key_hash, owner_hash = hashlib.sha256(key.encode()).hexdigest(), hashlib.sha256(owner.encode()).hexdigest()
        await self._session.execute(text("""
          INSERT INTO idempotency_records(tenant_id,operation,idempotency_key_hash,request_fingerprint,status,owner_token_hash,lease_expires_at,created_at,expires_at)
          VALUES(:tenant,:operation,:key_hash,:fingerprint,'in_progress',:owner_hash,:lease,:now,:expires)
          ON CONFLICT DO NOTHING
        """), {"tenant": self._tenant_id, "operation": operation, "key_hash": key_hash, "fingerprint": fingerprint, "owner_hash": owner_hash, "lease": now + timedelta(seconds=60), "now": now, "expires": now + timedelta(hours=24)})
        result = await self._session.execute(text("""
          SELECT * FROM idempotency_records WHERE tenant_id=:tenant AND operation=:operation
            AND idempotency_key_hash=:key_hash FOR UPDATE
        """), {"tenant": self._tenant_id, "operation": operation, "key_hash": key_hash})
        row = result.mappings().one()
        if row["request_fingerprint"] != fingerprint: return Reservation("fingerprint_conflict")
        if row["status"] == "completed":
            aad = f"{self._tenant_id}:{operation}:{key_hash}:{fingerprint}"
            return Reservation("replay", response_status=row["response_status"], response_headers=row["response_headers"], response_body=self._codec.decrypt(aad, row["response_envelope"]))
        if row["owner_token_hash"] == owner_hash: return Reservation("acquired", owner_token=owner)
        return Reservation("in_progress")

    async def complete(self, key: str, operation: str, fingerprint: str, owner_token: str, *, status: int, headers: Mapping[str, str], body: Mapping[str, Any]) -> bool:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        owner_hash = hashlib.sha256(owner_token.encode()).hexdigest()
        aad = f"{self._tenant_id}:{operation}:{key_hash}:{fingerprint}"
        safe_headers = {name: value for name, value in headers.items() if name.lower() in {"etag", "location", "content-type"}}
        result = await self._session.execute(text("""
          UPDATE idempotency_records SET status='completed',response_status=:status,
            response_headers=CAST(:headers AS jsonb),response_envelope=:envelope,completed_at=:now
          WHERE tenant_id=:tenant AND operation=:operation AND idempotency_key_hash=:key_hash
            AND request_fingerprint=:fingerprint AND owner_token_hash=:owner_hash
            AND status='in_progress' AND lease_expires_at>:now
        """), {"tenant": self._tenant_id, "operation": operation, "key_hash": key_hash, "fingerprint": fingerprint, "owner_hash": owner_hash, "status": status, "headers": safe_headers, "envelope": self._codec.encrypt(aad, body), "now": datetime.now(UTC)})
        return bool(getattr(result, "rowcount", 0) == 1)
