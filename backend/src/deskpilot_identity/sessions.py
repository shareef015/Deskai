from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import secrets
import time

from .audit import IdentityAuditLog
from .models import Principal, SessionRecord, SessionStatus


def _opaque_token() -> str:
    return secrets.token_urlsafe(48)


def _hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


class SessionError(RuntimeError):
    pass


class SessionStore:
    def __init__(self) -> None:
        self._by_id: dict[str, SessionRecord] = {}
        self._token_to_id: dict[str, str] = {}

    def put(self, record: SessionRecord) -> None:
        self._by_id[record.session_id] = record
        self._token_to_id[record.session_token_hash] = record.session_id

    def by_id(self, session_id: str) -> SessionRecord | None:
        return self._by_id.get(session_id)

    def by_token(self, token: str) -> SessionRecord | None:
        sid = self._token_to_id.get(_hash_token(token))
        return self._by_id.get(sid) if sid else None

    def remove_token(self, token_hash: str) -> None:
        self._token_to_id.pop(token_hash, None)

    def all(self) -> tuple[SessionRecord, ...]:
        return tuple(self._by_id.values())


class SessionManager:
    def __init__(
        self,
        *,
        store: SessionStore | None = None,
        audit: IdentityAuditLog | None = None,
        ttl_seconds: int = 8 * 60 * 60,
        max_concurrent_sessions: int = 3,
    ) -> None:
        self.store = store or SessionStore()
        self.audit = audit or IdentityAuditLog()
        self.ttl_seconds = ttl_seconds
        self.max_concurrent_sessions = max_concurrent_sessions

    def issue(self, principal: Principal, *, now: int | None = None, parent_session_id: str | None = None) -> tuple[str, SessionRecord]:
        ts = int(time.time()) if now is None else now
        token = _opaque_token()
        record = SessionRecord(
            session_id=secrets.token_urlsafe(24),
            session_token_hash=_hash_token(token),
            principal=principal,
            issued_at=ts,
            expires_at=ts + self.ttl_seconds,
            last_seen_at=ts,
            auth_version=1,
            permission_version=principal.permission_version,
            parent_session_id=parent_session_id,
        )
        self.store.put(record)
        self._enforce_concurrency(principal.subject, principal.tenant_id, now=ts, keep_session_id=record.session_id)
        self.audit.append("session.issued", actor_subject=principal.subject, tenant_id=principal.tenant_id, session_id=record.session_id, now=ts)
        return token, record

    def authenticate(self, token: str, *, now: int | None = None, touch: bool = True) -> SessionRecord:
        ts = int(time.time()) if now is None else now
        record = self.store.by_token(token)
        if record is None or not record.active(ts):
            raise SessionError("invalid_or_expired_session")
        if touch:
            record.last_seen_at = ts
        return record

    def rotate(self, token: str, *, now: int | None = None, reason: str = "authentication_boundary") -> tuple[str, SessionRecord]:
        ts = int(time.time()) if now is None else now
        old = self.authenticate(token, now=ts, touch=False)
        old_id = old.session_id
        principal = replace(old.principal, auth_time=ts)
        self.revoke_by_id(old_id, reason=f"rotated:{reason}", now=ts)
        new_token, new_record = self.issue(principal, now=ts, parent_session_id=old_id)
        new_record.auth_version = old.auth_version + 1
        self.audit.append("session.rotated", actor_subject=principal.subject, tenant_id=principal.tenant_id, session_id=new_record.session_id, details={"replaced_session_id": old_id, "reason": reason}, now=ts)
        return new_token, new_record

    def revoke_by_id(self, session_id: str, *, reason: str, now: int | None = None) -> bool:
        ts = int(time.time()) if now is None else now
        record = self.store.by_id(session_id)
        if record is None or record.status is not SessionStatus.ACTIVE:
            return False
        record.status = SessionStatus.REVOKED
        record.revoked_at = ts
        record.revoke_reason = reason
        self.store.remove_token(record.session_token_hash)
        self.audit.append("session.revoked", actor_subject=record.principal.subject, tenant_id=record.principal.tenant_id, session_id=record.session_id, details={"reason": reason}, now=ts)
        return True

    def revoke_subject(self, subject: str, tenant_id: str, *, reason: str, now: int | None = None) -> int:
        count = 0
        for record in self.store.all():
            if record.principal.subject == subject and record.principal.tenant_id == tenant_id:
                count += int(self.revoke_by_id(record.session_id, reason=reason, now=now))
        return count

    def revoke_oidc_sid(self, oidc_sid: str, *, reason: str, now: int | None = None) -> int:
        count = 0
        for record in self.store.all():
            if record.principal.oidc_sid == oidc_sid:
                count += int(self.revoke_by_id(record.session_id, reason=reason, now=now))
        return count

    def active_for_subject(self, subject: str, tenant_id: str, *, now: int) -> list[SessionRecord]:
        return sorted(
            [r for r in self.store.all() if r.principal.subject == subject and r.principal.tenant_id == tenant_id and r.active(now)],
            key=lambda r: (r.last_seen_at, r.issued_at, r.session_id),
        )

    def _enforce_concurrency(self, subject: str, tenant_id: str, *, now: int, keep_session_id: str) -> None:
        active = self.active_for_subject(subject, tenant_id, now=now)
        while len(active) > self.max_concurrent_sessions:
            victim = next((r for r in active if r.session_id != keep_session_id), active[0])
            self.revoke_by_id(victim.session_id, reason="concurrent_session_limit", now=now)
            active = self.active_for_subject(subject, tenant_id, now=now)
