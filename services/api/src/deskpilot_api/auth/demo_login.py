from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Mapping

from deskpilot_core.errors import DeskPilotError, ErrorCode


@dataclass(frozen=True, slots=True)
class DemoSession:
    session_id: str
    csrf_token: str
    persona_id: str
    tenant_id: str
    issued_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime


class DemoLoginBroker:
    """Creates opaque server-side demo sessions; never creates bearer tokens."""

    def __init__(self, identities: Mapping[str, Mapping[str, object]], *, environment: str, synthetic_mode: bool, trusted_origin: bool) -> None:
        self._identities = identities
        self._enabled = environment in {"development", "test"} and synthetic_mode and trusted_origin

    def login(self, persona_id: str, *, now: datetime | None = None) -> DemoSession:
        if not self._enabled:
            raise DeskPilotError(ErrorCode.ACCESS_DENIED)
        identity = self._identities.get(persona_id)
        if not identity or identity.get("account_enabled") is not True:
            raise DeskPilotError(ErrorCode.AUTHENTICATION_REQUIRED)
        instant = now or datetime.now(UTC)
        return DemoSession(
            session_id=secrets.token_urlsafe(32), csrf_token=secrets.token_urlsafe(32),
            persona_id=persona_id, tenant_id=str(identity["deskpilot_tenant_id"]), issued_at=instant,
            idle_expires_at=instant+timedelta(minutes=30), absolute_expires_at=instant+timedelta(minutes=120),
        )
