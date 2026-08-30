from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, ConfigDict, Field

from deskpilot_identity.policy import RequestContext
from deskpilot_identity.sessions import SessionManager

from .authorization import ObjectAuthorizer
from .errors import public_problem
from .mass_assignment import FieldPolicy, MassAssignmentViolation, accept_fields
from .middleware import ApiSecurityMiddleware
from .rate_limit import TokenBucketLimiter
from .repository import TenantRecord, TenantScopedRepository
from .tenant import TenantContext


class IncidentPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern=r"^(new|triaging|diagnosing|resolved|closed)$")


@dataclass(slots=True)
class ApiDependencies:
    sessions: SessionManager
    incidents: TenantScopedRepository[TenantRecord]
    csrf_secret: bytes


def build_secure_api(deps: ApiDependencies, *, allowed_hosts: list[str] | None = None) -> FastAPI:
    app = FastAPI(title="DeskPilot Secure API", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts or ["testserver", "localhost"])
    app.add_middleware(
        ApiSecurityMiddleware,
        sessions=deps.sessions,
        limiter=TokenBucketLimiter(capacity=30, refill_per_second=5),
        csrf_secret=deps.csrf_secret,
    )
    authorizer = ObjectAuthorizer()
    patch_policy = FieldPolicy.from_allowed({"title", "status"})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        code = {401: "unauthenticated", 403: "forbidden", 404: "not_found"}.get(exc.status_code, "request_rejected")
        problem = public_problem(exc.status_code, code, "Request rejected", correlation_id=correlation_id)
        return JSONResponse(problem.as_dict(), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        problem = public_problem(422, "validation_error", "Request validation failed", correlation_id=correlation_id)
        return JSONResponse(problem.as_dict(), status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        problem = public_problem(500, "internal_error", "Internal server error", correlation_id=correlation_id)
        return JSONResponse(problem.as_dict(), status_code=500)

    @app.get("/health/live")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/incidents/{incident_id}")
    async def get_incident(incident_id: str, request: Request) -> dict[str, object]:
        session = request.state.identity_session
        context = TenantContext.from_principal(session.principal)
        incident = deps.incidents.get(context, incident_id)
        if incident is None:
            raise HTTPException(status_code=404, detail="not_found")
        decision = authorizer.authorize(
            session.principal,
            action="incident:read",
            object_id=incident.id,
            object_tenant_id=incident.tenant_id,
            object_type="incident",
            request=RequestContext(device_trust="managed"),
        )
        if not decision.allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return {"id": incident.id, "tenantId": incident.tenant_id, **incident.payload}

    @app.patch("/api/incidents/{incident_id}")
    async def patch_incident(incident_id: str, body: IncidentPatch, request: Request) -> dict[str, object]:
        session = request.state.identity_session
        context = TenantContext.from_principal(session.principal)
        existing = deps.incidents.get(context, incident_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="not_found")
        decision = authorizer.authorize(
            session.principal,
            action="incident:update",
            object_id=existing.id,
            object_tenant_id=existing.tenant_id,
            object_type="incident",
            request=RequestContext(device_trust="managed"),
        )
        if not decision.allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        try:
            safe = accept_fields(body.model_dump(exclude_none=True), patch_policy)
        except MassAssignmentViolation as exc:
            raise HTTPException(status_code=400, detail="invalid_fields") from exc
        updated = deps.incidents.update_payload(context, incident_id, {**existing.payload, **safe})
        return {"id": updated.id, "tenantId": updated.tenant_id, **updated.payload}

    return app
