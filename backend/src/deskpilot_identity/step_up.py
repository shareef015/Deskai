from __future__ import annotations

import secrets
import time

from .models import SessionRecord, StepUpGrant


class StepUpError(RuntimeError):
    pass


class StepUpManager:
    def __init__(self, ttl_seconds: int = 5 * 60, *, allowed_acr_values: frozenset[str]) -> None:
        if not allowed_acr_values:
            raise ValueError("allowed_acr_values must explicitly define acceptable step-up assurance")
        self.ttl_seconds = ttl_seconds
        self.allowed_acr_values = allowed_acr_values
        self._grants: dict[str, StepUpGrant] = {}
        self._consumed: set[str] = set()

    def issue(
        self,
        session: SessionRecord,
        *,
        action: str,
        resource_id: str,
        verified_auth_time: int,
        acr: str | None,
        now: int | None = None,
    ) -> StepUpGrant:
        ts = int(time.time()) if now is None else now
        if verified_auth_time > ts + 60:
            raise StepUpError("step_up_authentication_time_invalid")
        if verified_auth_time < ts - self.ttl_seconds:
            raise StepUpError("step_up_authentication_too_old")
        if acr is None or acr not in self.allowed_acr_values:
            raise StepUpError("step_up_assurance_insufficient")
        grant = StepUpGrant(
            grant_id=secrets.token_urlsafe(32),
            session_id=session.session_id,
            action=action,
            resource_id=resource_id,
            tenant_id=session.principal.tenant_id,
            issued_at=ts,
            expires_at=ts + self.ttl_seconds,
            auth_time=verified_auth_time,
            acr=acr,
        )
        self._grants[grant.grant_id] = grant
        return grant

    def consume(self, grant_id: str, *, session: SessionRecord, action: str, resource_id: str, now: int | None = None) -> StepUpGrant:
        ts = int(time.time()) if now is None else now
        grant = self._grants.get(grant_id)
        if grant is None or grant_id in self._consumed:
            raise StepUpError("invalid_or_consumed_step_up_grant")
        if grant.expires_at <= ts:
            raise StepUpError("expired_step_up_grant")
        if grant.session_id != session.session_id or grant.tenant_id != session.principal.tenant_id:
            raise StepUpError("step_up_session_binding_mismatch")
        if grant.action != action or grant.resource_id != resource_id:
            raise StepUpError("step_up_scope_mismatch")
        if grant.one_time:
            self._consumed.add(grant_id)
        return grant
