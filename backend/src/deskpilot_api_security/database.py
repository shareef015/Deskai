from __future__ import annotations

from uuid import UUID


class DatabaseTenantError(ValueError):
    pass


def validate_tenant_uuid(tenant_id: str) -> str:
    try:
        return str(UUID(tenant_id))
    except ValueError as exc:
        raise DatabaseTenantError("invalid_tenant_id") from exc


def postgres_tenant_context_statement() -> str:
    """Parameterized PostgreSQL statement for transaction-scoped tenant context.

    Execute with the validated tenant UUID as parameter 1 on the same transaction/connection.
    Do not use string interpolation for tenant identifiers.
    """
    return "SELECT set_config('app.tenant_id', $1, true)"
