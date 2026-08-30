from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from deskpilot_core.errors import DeskPilotError, ErrorCode
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from deskpilot_api.auth.dependencies import require_principal
from deskpilot_api.incidents.schemas import IncidentCreate, IncidentPage, IncidentUpdate, IncidentView
from deskpilot_api.incidents.lifecycle import IncidentLifecycleService
from deskpilot_api.incidents.lifecycle_schemas import IncidentTransitionRequest
from deskpilot_api.incidents.service import IncidentService
from deskpilot_api.incidents.streaming import IncidentStreamService
from deskpilot_api.rate_limiting import enforce_rate_limit

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"], dependencies=[Depends(enforce_rate_limit)])


def get_incident_service(request: Request) -> IncidentService:
    service = getattr(request.app.state, "incident_service", None)
    if not isinstance(service, IncidentService):
        raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30)
    return service


def get_lifecycle_service(request: Request) -> IncidentLifecycleService:
    service = getattr(request.app.state, "incident_lifecycle_service", None)
    if not isinstance(service, IncidentLifecycleService):
        raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30)
    return service


def get_stream_service(request: Request) -> IncidentStreamService:
    service = getattr(request.app.state, "incident_stream_service", None)
    if not isinstance(service, IncidentStreamService):
        raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30)
    return service


@router.post("", response_model=IncidentView, status_code=status.HTTP_201_CREATED)
async def create_incident(command: IncidentCreate, principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)], service: Annotated[IncidentService, Depends(get_incident_service)], response: Response, idempotency_key: Annotated[str, Header(alias="Idempotency-Key")]) -> IncidentView:
    result = await service.create(principal, command, idempotency_key=idempotency_key)
    response.headers["ETag"] = f'"{result.version}"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/{incident_id}", response_model=IncidentView)
async def get_incident(incident_id: UUID, principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)], service: Annotated[IncidentService, Depends(get_incident_service)], response: Response) -> IncidentView:
    result = await service.get(principal, incident_id)
    response.headers["ETag"] = f'"{result.version}"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("", response_model=IncidentPage)
async def list_incidents(principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)], service: Annotated[IncidentService, Depends(get_incident_service)], response: Response, limit: Annotated[int, Query(ge=1, le=200)] = 50, cursor_opened_at: datetime | None = None, cursor_id: UUID | None = None) -> IncidentPage:
    if (cursor_opened_at is None) != (cursor_id is None):
        raise DeskPilotError(ErrorCode.VALIDATION_FAILED)
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(principal, limit=limit, cursor_opened_at=cursor_opened_at, cursor_id=cursor_id)


@router.patch("/{incident_id}", response_model=IncidentView)
async def update_incident(incident_id: UUID, command: IncidentUpdate, principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)], service: Annotated[IncidentService, Depends(get_incident_service)], response: Response, if_match: Annotated[str, Header(alias="If-Match")], idempotency_key: Annotated[str, Header(alias="Idempotency-Key")]) -> IncidentView:
    try:
        expected_version = int(if_match.strip('"'))
    except ValueError as exc:
        raise DeskPilotError(ErrorCode.VALIDATION_FAILED) from exc
    result = await service.update(principal, incident_id, command, expected_version=expected_version, idempotency_key=idempotency_key)
    response.headers["ETag"] = f'"{result.version}"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/{incident_id}/transitions", response_model=IncidentView)
async def transition_incident(
    incident_id: UUID,
    command: IncidentTransitionRequest,
    principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)],
    service: Annotated[IncidentLifecycleService, Depends(get_lifecycle_service)],
    request: Request,
    response: Response,
    if_match: Annotated[str, Header(alias="If-Match")],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> IncidentView:
    try:
        expected_version = int(if_match.strip('"'))
    except ValueError as exc:
        raise DeskPilotError(ErrorCode.VALIDATION_FAILED) from exc
    result = await service.transition(
        principal,
        incident_id,
        target=command.target,
        expected_version=expected_version,
        reason=command.reason,
        correlation_id=UUID(str(request.state.correlation_id)),
        idempotency_key=idempotency_key,
    )
    response.headers["ETag"] = f'"{result.version}"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/{incident_id}/events/stream")
async def stream_incident_events(
    incident_id: UUID,
    request: Request,
    principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)],
    service: Annotated[IncidentStreamService, Depends(get_stream_service)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    try:
        cursor = int(last_event_id) if last_event_id is not None else 0
        if cursor < 0:
            raise ValueError
    except ValueError as exc:
        raise DeskPilotError(ErrorCode.VALIDATION_FAILED) from exc
    await service.authorize(principal, incident_id)
    return StreamingResponse(
        service.stream(request, principal, incident_id, cursor),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"},
    )
