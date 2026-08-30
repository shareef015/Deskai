from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

import jwt

from deskpilot_core.errors import DeskPilotError, ErrorCode

from .claims import AuthenticatedPrincipal


class SigningKeyProvider(Protocol):
    async def get_key(self, token: str, *, refresh_on_miss: bool = True) -> Any: ...


class AccessTokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        key_provider: SigningKeyProvider,
        tenant_claim: str = "deskpilot_tenant_id",
        leeway_seconds: int = 60,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._keys = key_provider
        self._tenant_claim = tenant_claim
        self._leeway = leeway_seconds

    async def verify(self, token: str) -> AuthenticatedPrincipal:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") not in {"RS256", "ES256"} or not header.get("kid"):
                raise jwt.InvalidTokenError("algorithm or key id rejected")
            key = await self._keys.get_key(token, refresh_on_miss=True)
            claims: Mapping[str, Any] = jwt.decode(
                token,
                key=key,
                algorithms=[header["alg"]],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
            tenant_id = UUID(str(claims[self._tenant_claim]))
            scopes = _string_set(claims.get("scope", ""))
            roles = _string_set(claims.get("roles", ()))
            return AuthenticatedPrincipal(
                subject=str(claims["sub"]),
                tenant_id=tenant_id,
                issuer=str(claims["iss"]),
                audience=self._audience,
                scopes=scopes,
                roles=roles,
                token_id=str(claims["jti"]) if claims.get("jti") else None,
            )
        except (KeyError, TypeError, ValueError, jwt.PyJWTError) as exc:
            raise DeskPilotError(ErrorCode.AUTHENTICATION_REQUIRED) from exc


def _string_set(value: object) -> frozenset[str]:
    if isinstance(value, str):
        return frozenset(part for part in value.split() if part)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return frozenset(value)
    return frozenset()
