from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Request

from deskpilot_core.errors import DeskPilotError, ErrorCode
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from .service import AuthorizationGateway, UnitOfWorkFactory


class IncidentStreamService:
    def __init__(self, uow_factory: UnitOfWorkFactory, authorization: AuthorizationGateway) -> None:
        self._uow_factory = uow_factory
        self._authorization = authorization

    async def authorize(self, principal: AuthenticatedPrincipal, incident_id: UUID) -> None:
        await self._authorization.require(principal, "incident.read", "incident", incident_id)
        async with self._uow_factory(principal.tenant_id) as uow:
            if await uow.incidents.get(incident_id) is None:
                raise DeskPilotError(ErrorCode.RESOURCE_NOT_FOUND)

    async def stream(self, request: Request, principal: AuthenticatedPrincipal, incident_id: UUID, after_sequence: int) -> AsyncIterator[str]:
        cursor = after_sequence
        started = datetime.now(UTC)
        last_heartbeat = started
        while datetime.now(UTC) - started < timedelta(seconds=1800):
            if await request.is_disconnected():
                return
            async with self._uow_factory(principal.tenant_id) as uow:
                events = await uow.incidents.list_events_after(incident_id, cursor, limit=100)
            if events:
                for event in events:
                    cursor = event.sequence_number
                    payload = {"event_id": str(event.id), "incident_id": str(event.incident_id), "type": event.event_type, "schema_version": event.schema_version, "aggregate_version": event.aggregate_version, "occurred_at": event.occurred_at.isoformat(), "payload": event.payload}
                    yield _encode_sse(str(cursor), event.event_type, payload)
                last_heartbeat = datetime.now(UTC)
                continue
            now = datetime.now(UTC)
            if (now - last_heartbeat).total_seconds() >= 15:
                yield ": heartbeat\n\n"
                last_heartbeat = now
            await asyncio.sleep(1)


def _encode_sse(event_id: str, event_type: str, payload: dict[str, object]) -> str:
    safe_type = "".join(character for character in event_type if character.isalnum() or character in "._-")[:80]
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return f"id: {event_id}\nevent: {safe_type}\ndata: {data}\n\n"
