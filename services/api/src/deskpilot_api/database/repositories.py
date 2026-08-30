from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Incident, IncidentEvent


class IncidentRepository:
    """All reads and writes are constrained to the constructor's tenant."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _tenant_query(self) -> Select[tuple[Incident]]:
        return select(Incident).where(Incident.tenant_id == self._tenant_id)

    async def get(self, incident_id: UUID) -> Incident | None:
        statement = self._tenant_query().where(Incident.id == incident_id)
        return await self._session.scalar(statement)

    async def list_open(self, *, limit: int = 100) -> Sequence[Incident]:
        bounded_limit = min(max(limit, 1), 200)
        statement = (
            self._tenant_query()
            .where(Incident.closed_at.is_(None))
            .order_by(Incident.opened_at.desc())
            .limit(bounded_limit)
        )
        return (await self._session.scalars(statement)).all()

    async def list_page(
        self,
        *,
        limit: int,
        cursor_opened_at: datetime | None,
        cursor_id: UUID | None,
    ) -> Sequence[Incident]:
        bounded_limit = min(max(limit, 1), 200)
        statement = self._tenant_query()
        if cursor_opened_at is not None and cursor_id is not None:
            statement = statement.where(
                tuple_(Incident.opened_at, Incident.id) < tuple_(cursor_opened_at, cursor_id)
            )
        statement = statement.order_by(Incident.opened_at.desc(), Incident.id.desc()).limit(
            bounded_limit
        )
        return (await self._session.scalars(statement)).all()

    async def add(self, incident: Incident) -> None:
        if incident.tenant_id != self._tenant_id:
            raise ValueError("tenant mismatch")
        self._session.add(incident)
        await self._session.flush()

    async def update_status(
        self, incident_id: UUID, *, expected_version: int, new_status: str
    ) -> bool:
        incident = await self.get(incident_id)
        if incident is None or incident.version != expected_version:
            return False
        incident.status = new_status
        incident.version += 1
        await self._session.flush()
        return True

    async def update_details(
        self,
        incident_id: UUID,
        *,
        expected_version: int,
        priority: int | None,
        summary: str | None,
        updated_at: datetime,
    ) -> bool:
        values: dict[str, object] = {"updated_at": updated_at, "version": Incident.version + 1}
        if priority is not None:
            values["priority"] = priority
        if summary is not None:
            values["summary"] = summary
        statement = (
            update(Incident)
            .where(
                Incident.tenant_id == self._tenant_id,
                Incident.id == incident_id,
                Incident.version == expected_version,
            )
            .values(**values)
        )
        result = await self._session.execute(statement)
        return bool(getattr(result, "rowcount", 0) == 1)

    async def transition_status(
        self,
        incident_id: UUID,
        *,
        current_status: str,
        target_status: str,
        expected_version: int,
        updated_at: datetime,
    ) -> int | None:
        statement = (
            update(Incident)
            .where(
                Incident.tenant_id == self._tenant_id,
                Incident.id == incident_id,
                Incident.status == current_status,
                Incident.version == expected_version,
            )
            .values(
                status=target_status,
                updated_at=updated_at,
                closed_at=updated_at if target_status in {"resolved", "cancelled"} else None,
                version=Incident.version + 1,
            )
            .returning(Incident.version)
        )
        return await self._session.scalar(statement)

    async def add_event(self, event: IncidentEvent) -> None:
        if event.tenant_id != self._tenant_id:
            raise ValueError("tenant mismatch")
        self._session.add(event)
        await self._session.flush()

    async def list_events_after(
        self, incident_id: UUID, after_sequence: int, *, limit: int = 100
    ) -> Sequence[IncidentEvent]:
        statement = (
            select(IncidentEvent)
            .where(
                IncidentEvent.tenant_id == self._tenant_id,
                IncidentEvent.incident_id == incident_id,
                IncidentEvent.sequence_number > after_sequence,
            )
            .order_by(IncidentEvent.sequence_number)
            .limit(min(max(limit, 1), 100))
        )
        return (await self._session.scalars(statement)).all()
