from __future__ import annotations

from .audit import IdentityAuditLog
from .enforcement import EnforcementResult, IdentityEnforcer
from .models import PermissionSnapshot, Principal, SessionRecord
from .permission_drift import DriftResult, revoke_if_drifted
from .policy import RequestContext, ResourceContext
from .sessions import SessionManager
from .step_up import StepUpManager
from .token_vault import InMemoryTokenVault, ProviderTokenSet, TokenVaultError


class IdentityService:
    def __init__(
        self,
        *,
        sessions: SessionManager,
        enforcer: IdentityEnforcer,
        step_up: StepUpManager,
        audit: IdentityAuditLog,
        token_vault: InMemoryTokenVault | None = None,
    ) -> None:
        self.sessions = sessions
        self.enforcer = enforcer
        self.step_up = step_up
        self.audit = audit
        self.token_vault = token_vault or InMemoryTokenVault()

    def complete_login(self, principal: Principal, tokens: ProviderTokenSet | None, *, now: int) -> tuple[str, SessionRecord]:
        session_token, session = self.sessions.issue(principal, now=now)
        if tokens is not None:
            self.token_vault.bind(session.session_id, tokens)
        self.audit.append("login.completed", actor_subject=principal.subject, tenant_id=principal.tenant_id, session_id=session.session_id, now=now)
        return session_token, session

    def authorize(
        self, session_token: str, *, action: str, resource: ResourceContext, request: RequestContext,
        step_up_grant_id: str | None, now: int,
    ) -> EnforcementResult:
        result = self.enforcer.authorize(
            session_token, action=action, resource=resource, request=request, step_up_grant_id=step_up_grant_id, now=now
        )
        self.audit.append(
            "authorization.decision", actor_subject=result.session.principal.subject, tenant_id=result.session.principal.tenant_id,
            session_id=result.session.session_id, outcome="allow" if result.decision.allowed else "deny",
            details={"action": action, "resource_id": resource.resource_id, "reason": result.decision.reason}, now=now,
        )
        return result

    def apply_permission_snapshot(self, session: SessionRecord, snapshot: PermissionSnapshot, *, now: int) -> DriftResult:
        result = revoke_if_drifted(self.sessions, session, snapshot, now=now)
        if result.drifted:
            self.token_vault.revoke(session.session_id)
            self.audit.append("permission.drift", actor_subject=session.principal.subject, tenant_id=session.principal.tenant_id, session_id=session.session_id, outcome="revoked", details={"reason": result.reason}, now=now)
        return result

    def rotate_provider_tokens(self, session: SessionRecord, *, presented_refresh_token: str, replacement: ProviderTokenSet, now: int) -> None:
        try:
            family = self.token_vault.rotate(session.session_id, presented_refresh_token=presented_refresh_token, replacement=replacement)
        except TokenVaultError as exc:
            if str(exc) == "refresh_token_reuse_detected":
                self.sessions.revoke_by_id(session.session_id, reason="refresh_token_reuse", now=now)
                self.audit.append("token.refresh_reuse", actor_subject=session.principal.subject, tenant_id=session.principal.tenant_id, session_id=session.session_id, outcome="revoked", now=now)
            raise
        self.audit.append("token.rotated", actor_subject=session.principal.subject, tenant_id=session.principal.tenant_id, session_id=session.session_id, details={"generation": family.generation}, now=now)

    def logout_session(self, session: SessionRecord, *, now: int) -> None:
        self.sessions.revoke_by_id(session.session_id, reason="user_logout", now=now)
        self.token_vault.revoke(session.session_id)

    def logout_all(self, session: SessionRecord, *, now: int) -> int:
        subject = session.principal.subject
        tenant = session.principal.tenant_id
        ids = [r.session_id for r in self.sessions.active_for_subject(subject, tenant, now=now)]
        count = self.sessions.revoke_subject(subject, tenant, reason="user_logout_all", now=now)
        for sid in ids:
            self.token_vault.revoke(sid)
        return count
