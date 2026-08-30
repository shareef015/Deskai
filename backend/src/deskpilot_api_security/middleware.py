from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from deskpilot_identity.csrf import validate_csrf_token
from deskpilot_identity.http_contract import CSRF_COOKIE, SESSION_COOKIE
from deskpilot_identity.sessions import SessionError, SessionManager

from .errors import public_problem
from .rate_limit import TokenBucketLimiter
from .request_validation import RequestLimits, RequestValidationError, validate_request_id


PUBLIC_PATHS = frozenset({"/health/live", "/health/ready", "/api/auth/login", "/api/auth/callback", "/api/auth/backchannel-logout"})


def _rate_limit_family(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"api", "internal"}:
        return f"/{parts[0]}/{parts[1]}"
    return path


@dataclass(frozen=True, slots=True)
class ApiSecurityConfig:
    public_paths: frozenset[str] = PUBLIC_PATHS
    max_request_bytes: int = 1_048_576


class ApiSecurityMiddleware(BaseHTTPMiddleware):
    """Request boundary: correlation ID, request limits, authentication and abuse control."""

    def __init__(self, app, *, sessions: SessionManager, limiter: TokenBucketLimiter, csrf_secret: bytes, config: ApiSecurityConfig | None = None) -> None:
        super().__init__(app)
        self.sessions = sessions
        self.limiter = limiter
        if len(csrf_secret) < 16:
            raise ValueError("csrf_secret_too_short")
        self.csrf_secret = csrf_secret
        self.config = config or ApiSecurityConfig()
        self.limits = RequestLimits(max_content_length=self.config.max_request_bytes)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_request_id = request.headers.get("x-request-id")
        try:
            validate_request_id(incoming_request_id)
            content_length = request.headers.get("content-length")
            self.limits.validate(
                method=request.method,
                content_length=int(content_length) if content_length is not None else None,
                content_type=request.headers.get("content-type"),
            )
        except (RequestValidationError, ValueError):
            problem = public_problem(400, "invalid_request", "Request rejected")
            return JSONResponse(problem.as_dict(), status_code=400)

        correlation_id = incoming_request_id or secrets.token_hex(12)
        request.state.correlation_id = correlation_id

        if request.url.path not in self.config.public_paths:
            token = request.cookies.get(SESSION_COOKIE)
            if not token:
                problem = public_problem(401, "unauthenticated", "Authentication required", correlation_id=correlation_id)
                return JSONResponse(problem.as_dict(), status_code=401)
            try:
                session = self.sessions.authenticate(token)
            except SessionError:
                problem = public_problem(401, "invalid_session", "Authentication required", correlation_id=correlation_id)
                return JSONResponse(problem.as_dict(), status_code=401)
            request.state.identity_session = session
            principal = session.principal
            if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
                header_token = request.headers.get("x-csrf-token")
                cookie_token = request.cookies.get(CSRF_COOKIE)
                if (
                    not header_token
                    or not cookie_token
                    or header_token != cookie_token
                    or not validate_csrf_token(header_token, session.session_id, self.csrf_secret)
                ):
                    problem = public_problem(403, "csrf_rejected", "Request verification failed", correlation_id=correlation_id)
                    return JSONResponse(problem.as_dict(), status_code=403)
            family = _rate_limit_family(request.url.path)
            rate_key = f"{principal.tenant_id}:{principal.subject}:{family}:{request.method}"
            limit = self.limiter.check(rate_key)
            if not limit.allowed:
                problem = public_problem(429, "rate_limited", "Too many requests", correlation_id=correlation_id)
                response = JSONResponse(problem.as_dict(), status_code=429)
                response.headers["Retry-After"] = str(limit.retry_after_seconds)
                return response

        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        response.headers["Cache-Control"] = "no-store"
        return response
