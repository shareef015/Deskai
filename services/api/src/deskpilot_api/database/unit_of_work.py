from __future__ import annotations

from types import TracebackType
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories import IncidentRepository
from .tenant_context import bind_tenant_context, verify_tenant_context


class SqlAlchemyUnitOfWork:
    def __init__(self, factory: async_sessionmaker[AsyncSession], tenant_id: UUID) -> None:
        self._factory = factory
        self._tenant_id = tenant_id
        self.session: AsyncSession
        self.incidents: IncidentRepository

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._factory()
        await bind_tenant_context(self.session, self._tenant_id)
        await verify_tenant_context(self.session, self._tenant_id)
        self.incidents = IncidentRepository(self.session, self._tenant_id)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
