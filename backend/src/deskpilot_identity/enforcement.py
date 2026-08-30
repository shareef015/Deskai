from __future__ import annotations

from dataclasses import dataclass

from .policy import AuthorizationPolicy, PolicyDecision, RequestContext, ResourceContext
from .sessions import SessionManager, SessionRecord
from .step_up import StepUpError, StepUpManager


@dataclass(frozen=True, slots=True)
class EnforcementResult:
    session: SessionRecord
    decision: PolicyDecision


class IdentityEnforcer:
    def __init__(self, sessions: SessionManager, policy: AuthorizationPolicy, step_up: StepUpManager) -> None:
        self.sessions = sessions
        self.policy = policy
        self.step_up = step_up

    def authorize(
        self,
        session_token: str,
        *,
        action: str,
        resource: ResourceContext,
        request: RequestContext,
        step_up_grant_id: str | None = None,
        now: int,
    ) -> EnforcementResult:
        session = self.sessions.authenticate(session_token, now=now)
        effective_request = request
        preliminary = self.policy.evaluate(session.principal, action, resource, request)
        if preliminary.requires_step_up and not preliminary.allowed:
            if step_up_grant_id is None:
                return EnforcementResult(session, preliminary)
            try:
                self.step_up.consume(step_up_grant_id, session=session, action=action, resource_id=resource.resource_id, now=now)
            except StepUpError:
                return EnforcementResult(session, PolicyDecision(False, "invalid_step_up_grant", requires_step_up=True))
            effective_request = RequestContext(
                client_ip=request.client_ip,
                device_trust=request.device_trust,
                risk_level=request.risk_level,
                step_up_verified=True,
            )
        return EnforcementResult(session, self.policy.evaluate(session.principal, action, resource, effective_request))
