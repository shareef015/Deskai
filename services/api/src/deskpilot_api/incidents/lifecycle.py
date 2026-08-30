from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from deskpilot_core.errors import DeskPilotError, ErrorCode
from deskpilot_api.audit.service import AuditAppendRequest, AuditWriter
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from .events import IncidentEventEnvelope, IncidentEventService
from deskpilot_api.idempotency import IdempotencyCodec, IdempotencyStore, request_fingerprint
from .schemas import IncidentView
from .service import AuthorizationGateway, UnitOfWorkFactory
from .state_machine import decide_transition


class LifecycleGuardProvider(Protocol):
    async def satisfied_guards(self, tenant_id: UUID, incident_id: UUID, target: str) -> frozenset[str]: ...


class IncidentLifecycleService:
    def __init__(self, uow_factory: UnitOfWorkFactory, authorization: AuthorizationGateway, guards: LifecycleGuardProvider, idempotency_codec: IdempotencyCodec) -> None:
        self._uow_factory = uow_factory
        self._authorization = authorization
        self._guards = guards
        self._idempotency_codec = idempotency_codec

    async def transition(self, principal: AuthenticatedPrincipal, incident_id: UUID, *, target: str, expected_version: int, reason: str | None, correlation_id: UUID, idempotency_key: str) -> IncidentView:
        await self._authorization.require(principal, "incident.transition", "incident", incident_id)
        satisfied = await self._guards.satisfied_guards(principal.tenant_id, incident_id, target)
        if target == "escalated" and reason:
            satisfied = satisfied | {"escalation_reason_recorded"}
        async with self._uow_factory(principal.tenant_id) as uow:
            store = IdempotencyStore(uow.session, principal.tenant_id, self._idempotency_codec)
            operation = f"incident.transition:{incident_id}"
            fingerprint = request_fingerprint("POST", "/api/v1/incidents/{incident_id}/transitions", {"target": target, "reason": reason}, {"if_match": expected_version})
            reservation = await store.reserve(idempotency_key, operation, fingerprint)
            if reservation.state == "replay" and reservation.response_body is not None:
                return IncidentView.model_validate(reservation.response_body)
            if reservation.state != "acquired" or reservation.owner_token is None:
                raise DeskPilotError(ErrorCode.CONFLICT)
            current = await uow.incidents.get(incident_id)
            if current is None:
                raise DeskPilotError(ErrorCode.RESOURCE_NOT_FOUND)
            decision = decide_transition(current.status, target, satisfied)
            if not decision.allowed:
                raise DeskPilotError(ErrorCode.CONFLICT)
            changed = await uow.incidents.transition_status(incident_id, current_status=current.status, target_status=target, expected_version=expected_version, updated_at=datetime.now(UTC))
            if changed is None:
                raise DeskPilotError(ErrorCode.CONFLICT)
            await IncidentEventService(uow.session, principal.tenant_id).append(
                IncidentEventEnvelope(
                    tenant_id=principal.tenant_id,
                    incident_id=incident_id,
                    event_type="incident_status_transitioned",
                    aggregate_version=changed,
                    actor_type="employee",
                    actor_id=None,
                    correlation_id=correlation_id,
                    causation_id=None,
                    payload={"from": current.status, "to": target, "reason": reason},
                )
            )
            await AuditWriter(uow.session).append(AuditAppendRequest(tenant_id=principal.tenant_id, event_type="incident_status_transitioned", actor_type="human", actor_id=None, resource_type="incident", resource_id=incident_id, correlation_id=correlation_id, payload={"from": current.status, "to": target}))
            incident = await uow.incidents.get(incident_id)
            if incident is None:
                raise DeskPilotError(ErrorCode.INTERNAL_ERROR)
            view = IncidentView.model_validate(incident)
            await store.complete(idempotency_key, operation, fingerprint, reservation.owner_token, status=200, headers={"etag": f'"{view.version}"'}, body=view.model_dump(mode="json"))
            await uow.commit()
        return view
