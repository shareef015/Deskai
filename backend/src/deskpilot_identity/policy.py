from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import Principal, Role


ROLE_CAPABILITIES: Mapping[Role, frozenset[str]] = {
    Role.VIEWER: frozenset({"incident:read"}),
    Role.SERVICE_DESK: frozenset({"incident:read", "incident:update", "diagnostic:run", "remediation:request"}),
    Role.SENIOR_ENGINEER: frozenset({"incident:read", "incident:update", "diagnostic:run", "remediation:request"}),
    Role.APPROVER: frozenset({"incident:read", "remediation:approve"}),
    Role.TENANT_ADMIN: frozenset({"incident:read", "incident:update", "diagnostic:run", "remediation:request", "remediation:approve", "tenant:manage"}),
    Role.PLATFORM_ADMIN: frozenset({"platform:manage"}),
}


@dataclass(frozen=True, slots=True)
class ResourceContext:
    tenant_id: str
    resource_type: str
    resource_id: str
    owner_user_id: str | None = None
    classification: str = "internal"


@dataclass(frozen=True, slots=True)
class RequestContext:
    client_ip: str | None = None
    device_trust: str = "unknown"
    risk_level: str = "normal"
    step_up_verified: bool = False


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_step_up: bool = False


class AuthorizationPolicy:
    """Deny-by-default RBAC + ABAC policy. Backend enforcement is authoritative."""

    STEP_UP_ACTIONS = frozenset({"remediation:approve", "remediation:execute", "tenant:manage", "platform:manage"})

    def evaluate(self, principal: Principal | None, action: str, resource: ResourceContext, request: RequestContext) -> PolicyDecision:
        if principal is None:
            return PolicyDecision(False, "unauthenticated")
        if principal.tenant_id != resource.tenant_id and Role.PLATFORM_ADMIN not in principal.roles:
            return PolicyDecision(False, "cross_tenant_denied")

        effective = set(principal.capabilities)
        for role in principal.roles:
            effective.update(ROLE_CAPABILITIES.get(role, frozenset()))
        if action not in effective:
            return PolicyDecision(False, "capability_denied")

        if request.risk_level == "blocked":
            return PolicyDecision(False, "risk_policy_denied")
        if resource.classification == "restricted" and request.device_trust != "managed":
            return PolicyDecision(False, "managed_device_required")

        needs_step_up = action in self.STEP_UP_ACTIONS or request.risk_level == "elevated"
        if needs_step_up and not request.step_up_verified:
            return PolicyDecision(False, "step_up_required", requires_step_up=True)
        return PolicyDecision(True, "allowed", requires_step_up=needs_step_up)
