from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Generic, TypeVar

from .tenant import TenantContext, TenantGuard, TenantViolation


@dataclass(frozen=True, slots=True)
class TenantRecord:
    id: str
    tenant_id: str
    payload: dict[str, object]


T = TypeVar("T", bound=TenantRecord)


class TenantScopedRepository(Generic[T]):
    """Reference repository whose API makes a TenantContext mandatory for every operation."""

    def __init__(self, seed: list[T] | None = None) -> None:
        self._rows: dict[str, T] = {row.id: row for row in (seed or [])}

    def get(self, context: TenantContext, record_id: str) -> T | None:
        row = self._rows.get(record_id)
        if row is None:
            return None
        # Return indistinguishable not-found across tenant boundaries to avoid object enumeration.
        if row.tenant_id != context.tenant_id:
            return None
        return row

    def list(self, context: TenantContext) -> tuple[T, ...]:
        return tuple(row for row in self._rows.values() if row.tenant_id == context.tenant_id)

    def insert(self, context: TenantContext, row: T) -> T:
        TenantGuard.require_same_tenant(context, row.tenant_id)
        if row.id in self._rows:
            raise ValueError("record_exists")
        self._rows[row.id] = row
        return row

    def update_payload(self, context: TenantContext, record_id: str, payload: dict[str, object]) -> T:
        row = self._rows.get(record_id)
        if row is None or row.tenant_id != context.tenant_id:
            raise KeyError("record_not_found")
        # tenant_id is immutable and never accepted from the payload.
        updated = replace(row, payload=dict(payload))
        self._rows[record_id] = updated
        return updated

    def delete(self, context: TenantContext, record_id: str) -> None:
        row = self._rows.get(record_id)
        if row is None or row.tenant_id != context.tenant_id:
            raise KeyError("record_not_found")
        del self._rows[record_id]
