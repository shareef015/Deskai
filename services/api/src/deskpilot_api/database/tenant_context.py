from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def bind_tenant_context(session: AsyncSession, tenant_id: UUID) -> None:
    """Bind RLS scope to the current transaction without SQL interpolation."""
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


async def verify_tenant_context(session: AsyncSession, expected: UUID) -> None:
    value = await session.scalar(text("SELECT current_setting('app.tenant_id', true)"))
    if value != str(expected):
        raise RuntimeError("database tenant context was not established")
