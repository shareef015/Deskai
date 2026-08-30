from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import FrozenSet, Mapping


class Role(StrEnum):
    VIEWER = "viewer"
    SERVICE_DESK = "service_desk"
    SENIOR_ENGINEER = "senior_engineer"
    APPROVER = "approver"
    TENANT_ADMIN = "tenant_admin"
    PLATFORM_ADMIN = "platform_admin"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    tenant_id: str
    subject: str
    roles: FrozenSet[Role]
    capabilities: FrozenSet[str]
    attributes: Mapping[str, str] = field(default_factory=dict)
    auth_time: int = 0
    acr: str | None = None
    amr: tuple[str, ...] = ()
    oidc_sid: str | None = None
    permission_version: int = 1


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    session_token_hash: str
    principal: Principal
    issued_at: int
    expires_at: int
    last_seen_at: int
    auth_version: int
    permission_version: int
    status: SessionStatus = SessionStatus.ACTIVE
    revoked_at: int | None = None
    revoke_reason: str | None = None
    parent_session_id: str | None = None

    def active(self, now: int) -> bool:
        return self.status is SessionStatus.ACTIVE and self.expires_at > now


@dataclass(frozen=True, slots=True)
class StepUpGrant:
    grant_id: str
    session_id: str
    action: str
    resource_id: str
    tenant_id: str
    issued_at: int
    expires_at: int
    auth_time: int
    acr: str | None
    one_time: bool = True


@dataclass(frozen=True, slots=True)
class PermissionSnapshot:
    subject: str
    tenant_id: str
    roles: FrozenSet[Role]
    capabilities: FrozenSet[str]
    permission_version: int
