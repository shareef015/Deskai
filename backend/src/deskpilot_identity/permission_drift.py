from __future__ import annotations

from dataclasses import dataclass

from .models import PermissionSnapshot, SessionRecord
from .sessions import SessionManager


@dataclass(frozen=True, slots=True)
class DriftResult:
    drifted: bool
    reason: str


def detect_permission_drift(session: SessionRecord, source: PermissionSnapshot) -> DriftResult:
    principal = session.principal
    if principal.subject != source.subject or principal.tenant_id != source.tenant_id:
        return DriftResult(True, "identity_binding_changed")
    if session.permission_version != source.permission_version:
        return DriftResult(True, "permission_version_changed")
    if principal.roles != source.roles:
        return DriftResult(True, "role_membership_changed")
    if principal.capabilities != source.capabilities:
        return DriftResult(True, "capabilities_changed")
    return DriftResult(False, "unchanged")


def revoke_if_drifted(manager: SessionManager, session: SessionRecord, source: PermissionSnapshot, *, now: int) -> DriftResult:
    result = detect_permission_drift(session, source)
    if result.drifted:
        manager.revoke_by_id(session.session_id, reason=f"permission_drift:{result.reason}", now=now)
    return result
