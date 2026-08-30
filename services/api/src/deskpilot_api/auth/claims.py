from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    subject: str
    tenant_id: UUID
    issuer: str
    audience: str
    scopes: frozenset[str]
    roles: frozenset[str]
    token_id: str | None = None

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes
