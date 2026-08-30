from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from deskpilot_core.errors import DeskPilotError, ErrorCode

from .claims import AuthenticatedPrincipal
from .verifier import AccessTokenVerifier


bearer = HTTPBearer(auto_error=False)


def get_verifier(request: Request) -> AccessTokenVerifier:
    verifier = getattr(request.app.state, "access_token_verifier", None)
    if not isinstance(verifier, AccessTokenVerifier):
        raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30)
    return verifier


async def require_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    verifier: Annotated[AccessTokenVerifier, Depends(get_verifier)],
    request: Request,
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise DeskPilotError(ErrorCode.AUTHENTICATION_REQUIRED)
    principal = await verifier.verify(credentials.credentials)
    request.state.principal = principal
    request.state.tenant_id = principal.tenant_id
    return principal
