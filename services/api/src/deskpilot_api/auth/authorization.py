from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from deskpilot_core.errors import DeskPilotError, ErrorCode

from .claims import AuthenticatedPrincipal
from .dependencies import require_principal


def require_scope(scope: str) -> Callable[..., AuthenticatedPrincipal]:
    async def dependency(
        principal: Annotated[AuthenticatedPrincipal, Depends(require_principal)],
    ) -> AuthenticatedPrincipal:
        if not principal.has_scope(scope):
            raise DeskPilotError(ErrorCode.ACCESS_DENIED)
        return principal

    return dependency
