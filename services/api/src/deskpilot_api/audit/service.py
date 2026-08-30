from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


PROHIBITED_KEYS = frozenset(
    {"password", "authorization", "cookie", "access_token", "private_key", "hidden_reasoning"}
)


@dataclass(frozen=True, slots=True)
class AuditAppendRequest:
    tenant_id: UUID
    event_type: str
    actor_type: str
    actor_id: UUID | None
    resource_type: str
    resource_id: UUID
    correlation_id: UUID
    payload: Mapping[str, Any]

    def safe_payload(self) -> Mapping[str, Any]:
        lowered = {str(key).lower() for key in self.payload}
        if lowered & PROHIBITED_KEYS:
            raise ValueError("prohibited audit payload field")
        return MappingProxyType(dict(self.payload))


class AuditWriter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, request: AuditAppendRequest) -> UUID:
        statement = text(
            "SELECT event_id FROM append_audit_event(:tenant_id, :event_type, :actor_type, "
            ":actor_id, :resource_type, :resource_id, :correlation_id, CAST(:payload AS jsonb))"
        )
        event_id = await self._session.scalar(
            statement,
            {
                "tenant_id": request.tenant_id,
                "event_type": request.event_type,
                "actor_type": request.actor_type,
                "actor_id": request.actor_id,
                "resource_type": request.resource_type,
                "resource_id": request.resource_id,
                "correlation_id": request.correlation_id,
                "payload": dict(request.safe_payload()),
            },
        )
        if not isinstance(event_id, UUID):
            raise RuntimeError("audit append did not return an event identifier")
        return event_id
