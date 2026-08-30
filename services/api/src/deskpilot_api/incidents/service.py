from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from deskpilot_core.errors import DeskPilotError, ErrorCode
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from deskpilot_api.database.models import Incident
from deskpilot_api.database.unit_of_work import SqlAlchemyUnitOfWork
from deskpilot_api.idempotency import IdempotencyCodec, IdempotencyStore, request_fingerprint
from .schemas import IncidentCreate, IncidentPage, IncidentUpdate, IncidentView
from .priority import PrioritySignals, classify_priority


class AuthorizationGateway(Protocol):
    async def require(self, principal: AuthenticatedPrincipal, action: str, resource_type: str, resource_id: UUID | None) -> None: ...


UnitOfWorkFactory = Callable[[UUID], SqlAlchemyUnitOfWork]


class IncidentService:
    def __init__(self, uow_factory: UnitOfWorkFactory, authorization: AuthorizationGateway, idempotency_codec: IdempotencyCodec) -> None:
        self._uow_factory = uow_factory
        self._authorization = authorization
        self._idempotency_codec = idempotency_codec

    async def create(self, principal: AuthenticatedPrincipal, command: IncidentCreate, *, idempotency_key: str) -> IncidentView:
        await self._authorization.require(principal, "incident.create", "incident", None)
        now = datetime.now(UTC)
        decision = classify_priority(PrioritySignals(command.impact_score, command.urgency_score, command.affected_user_count, command.business_critical_service, command.security_or_safety_risk, command.complete_site_outage))
        incident = Incident(id=uuid4(), tenant_id=principal.tenant_id, requester_id=command.requester_id, device_id=command.device_id, category=command.category, status="new", priority=decision.priority, severity=decision.severity, impact_score=decision.impact_score, urgency_score=decision.urgency_score, priority_policy_version=decision.policy_version, priority_rationale=list(decision.reason_codes), priority_calculated_at=now, summary=command.summary, version=1, opened_at=now, updated_at=now, closed_at=None)
        async with self._uow_factory(principal.tenant_id) as uow:
            store = IdempotencyStore(uow.session, principal.tenant_id, self._idempotency_codec)
            fingerprint = request_fingerprint("POST", "/api/v1/incidents", command.model_dump(mode="json"), {})
            reservation = await store.reserve(idempotency_key, "incident.create", fingerprint)
            if reservation.state == "replay" and reservation.response_body is not None:
                return IncidentView.model_validate(reservation.response_body)
            if reservation.state != "acquired" or reservation.owner_token is None:
                raise DeskPilotError(ErrorCode.CONFLICT)
            await uow.incidents.add(incident)
            view = IncidentView.model_validate(incident)
            await store.complete(idempotency_key, "incident.create", fingerprint, reservation.owner_token, status=201, headers={"etag": f'"{view.version}"'}, body=view.model_dump(mode="json"))
            await uow.commit()
        return view

    async def get(self, principal: AuthenticatedPrincipal, incident_id: UUID) -> IncidentView:
        await self._authorization.require(principal, "incident.read", "incident", incident_id)
        async with self._uow_factory(principal.tenant_id) as uow:
            incident = await uow.incidents.get(incident_id)
        if incident is None:
            raise DeskPilotError(ErrorCode.RESOURCE_NOT_FOUND)
        return IncidentView.model_validate(incident)

    async def list(self, principal: AuthenticatedPrincipal, *, limit: int, cursor_opened_at: datetime | None, cursor_id: UUID | None) -> IncidentPage:
        await self._authorization.require(principal, "incident.list", "incident", None)
        async with self._uow_factory(principal.tenant_id) as uow:
            rows = await uow.incidents.list_page(limit=limit, cursor_opened_at=cursor_opened_at, cursor_id=cursor_id)
        items = tuple(IncidentView.model_validate(row) for row in rows)
        next_cursor = None
        if len(items) == limit and items:
            last = items[-1]
            next_cursor = f"{last.opened_at.isoformat()}|{last.id}"
        return IncidentPage(items=items, next_cursor=next_cursor)

    async def update(self, principal: AuthenticatedPrincipal, incident_id: UUID, command: IncidentUpdate, *, expected_version: int, idempotency_key: str) -> IncidentView:
        await self._authorization.require(principal, "incident.update", "incident", incident_id)
        if command.summary is None:
            raise DeskPilotError(ErrorCode.VALIDATION_FAILED)
        async with self._uow_factory(principal.tenant_id) as uow:
            store = IdempotencyStore(uow.session, principal.tenant_id, self._idempotency_codec)
            operation = f"incident.update:{incident_id}"
            fingerprint = request_fingerprint("PATCH", "/api/v1/incidents/{incident_id}", command.model_dump(mode="json"), {"if_match": expected_version})
            reservation = await store.reserve(idempotency_key, operation, fingerprint)
            if reservation.state == "replay" and reservation.response_body is not None:
                return IncidentView.model_validate(reservation.response_body)
            if reservation.state != "acquired" or reservation.owner_token is None:
                raise DeskPilotError(ErrorCode.CONFLICT)
            changed = await uow.incidents.update_details(incident_id, expected_version=expected_version, priority=None, summary=command.summary, updated_at=datetime.now(UTC))
            if not changed:
                raise DeskPilotError(ErrorCode.CONFLICT)
            incident = await uow.incidents.get(incident_id)
            if incident is None:
                raise DeskPilotError(ErrorCode.RESOURCE_NOT_FOUND)
            view = IncidentView.model_validate(incident)
            await store.complete(idempotency_key, operation, fingerprint, reservation.owner_token, status=200, headers={"etag": f'"{view.version}"'}, body=view.model_dump(mode="json"))
            await uow.commit()
        return view
