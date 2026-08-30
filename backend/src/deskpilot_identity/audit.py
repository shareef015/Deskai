from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import time
from typing import Any


@dataclass(frozen=True, slots=True)
class IdentityAuditEvent:
    sequence: int
    occurred_at: int
    event_type: str
    actor_subject: str | None
    tenant_id: str | None
    session_id: str | None
    outcome: str
    details: dict[str, Any]
    previous_hash: str
    event_hash: str


class IdentityAuditLog:
    """Small append-only hash-chained audit abstraction. Persist this to durable audit storage in production."""

    def __init__(self) -> None:
        self._events: list[IdentityAuditEvent] = []

    def append(
        self,
        event_type: str,
        *,
        actor_subject: str | None = None,
        tenant_id: str | None = None,
        session_id: str | None = None,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
        now: int | None = None,
    ) -> IdentityAuditEvent:
        ts = int(time.time()) if now is None else now
        previous_hash = self._events[-1].event_hash if self._events else "GENESIS"
        body = {
            "sequence": len(self._events) + 1,
            "occurred_at": ts,
            "event_type": event_type,
            "actor_subject": actor_subject,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "outcome": outcome,
            "details": details or {},
            "previous_hash": previous_hash,
        }
        digest = sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        event = IdentityAuditEvent(event_hash=digest, **body)
        self._events.append(event)
        return event

    def verify_chain(self) -> bool:
        previous = "GENESIS"
        for event in self._events:
            body = asdict(event)
            digest = body.pop("event_hash")
            if body["previous_hash"] != previous:
                return False
            calculated = sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if calculated != digest:
                return False
            previous = digest
        return True

    def events(self) -> tuple[IdentityAuditEvent, ...]:
        return tuple(self._events)
