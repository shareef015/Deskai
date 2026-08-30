from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from deskpilot_api.database.models import EventOutbox, IncidentEvent

PROHIBITED_KEYS = frozenset({"password", "authorization", "cookie", "access_token", "private_key", "hidden_reasoning"})
ALLOWED_TOPICS = frozenset({"deskpilot.incident.events.v1"})


@dataclass(frozen=True, slots=True)
class IncidentEventEnvelope:
    tenant_id: UUID
    incident_id: UUID
    event_type: str
    aggregate_version: int
    actor_type: str
    actor_id: UUID | None
    correlation_id: UUID
    causation_id: UUID | None
    payload: Mapping[str, Any]
    schema_version: str = "1"


class IncidentEventService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def append(self, envelope: IncidentEventEnvelope, *, topic: str = "deskpilot.incident.events.v1") -> UUID:
        if envelope.tenant_id != self._tenant_id or topic not in ALLOWED_TOPICS:
            raise ValueError("incident event scope or topic rejected")
        if envelope.aggregate_version < 1:
            raise ValueError("aggregate version must be positive")
        lowered = {str(key).lower() for key in envelope.payload}
        if lowered & PROHIBITED_KEYS:
            raise ValueError("prohibited incident event field")
        payload = dict(envelope.payload)
        if len(json.dumps(payload, separators=(",", ":")).encode()) > 65_536:
            raise ValueError("incident event payload too large")
        now = datetime.now(UTC)
        event_id = uuid4()
        event = IncidentEvent(id=event_id, tenant_id=self._tenant_id, incident_id=envelope.incident_id, sequence_number=envelope.aggregate_version, event_type=envelope.event_type, schema_version=envelope.schema_version, aggregate_version=envelope.aggregate_version, actor_type=envelope.actor_type, actor_id=envelope.actor_id, correlation_id=envelope.correlation_id, causation_id=envelope.causation_id, payload=payload, occurred_at=now)
        outbox = EventOutbox(id=uuid4(), tenant_id=self._tenant_id, incident_event_id=event_id, topic=topic, partition_key=str(envelope.incident_id), schema_version=envelope.schema_version, payload={"event_id": str(event_id), "tenant_id": str(self._tenant_id), "incident_id": str(envelope.incident_id), "event_type": envelope.event_type, "aggregate_version": envelope.aggregate_version, "correlation_id": str(envelope.correlation_id), "causation_id": str(envelope.causation_id) if envelope.causation_id else None, "occurred_at": now.isoformat(), "payload": payload}, created_at=now, available_at=now, claimed_at=None, published_at=None, attempt_count=0, last_error_code=None, dead_lettered_at=None)
        self._session.add_all((event, outbox))
        await self._session.flush()
        return event_id
