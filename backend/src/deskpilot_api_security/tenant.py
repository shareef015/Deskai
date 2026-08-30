from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from deskpilot_identity.models import Principal, Role


class TenantViolation(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: str
    subject: str
    platform_admin: bool = False

    @classmethod
    def from_principal(cls, principal: Principal) -> "TenantContext":
        return cls(
            tenant_id=principal.tenant_id,
            subject=principal.subject,
            platform_admin=Role.PLATFORM_ADMIN in principal.roles,
        )


class TenantOwned(Protocol):
    tenant_id: str


T = TypeVar("T", bound=TenantOwned)


class TenantGuard:
    """Central cross-tenant guard. Platform-admin bypass must be explicit at each call site."""

    @staticmethod
    def require_same_tenant(context: TenantContext, resource_tenant_id: str, *, allow_platform_admin: bool = False) -> None:
        if context.tenant_id == resource_tenant_id:
            return
        if allow_platform_admin and context.platform_admin:
            return
        raise TenantViolation("cross_tenant_access_denied")

    @classmethod
    def filter_rows(cls, context: TenantContext, rows: list[T]) -> list[T]:
        # Deliberately no platform-admin bypass here: generic tenant repositories always scope.
        return [row for row in rows if row.tenant_id == context.tenant_id]
