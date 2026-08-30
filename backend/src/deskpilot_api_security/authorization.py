from __future__ import annotations

from dataclasses import dataclass

from deskpilot_identity.models import Principal
from deskpilot_identity.policy import AuthorizationPolicy, RequestContext, ResourceContext


@dataclass(frozen=True, slots=True)
class ObjectAccessDecision:
    allowed: bool
    reason: str


class ObjectAuthorizer:
    """BOLA/BFLA defense: authorize the concrete object, not only the route/function."""

    def __init__(self, policy: AuthorizationPolicy | None = None) -> None:
        self._policy = policy or AuthorizationPolicy()

    def authorize(
        self,
        principal: Principal | None,
        *,
        action: str,
        object_id: str,
        object_tenant_id: str,
        object_type: str,
        owner_user_id: str | None = None,
        classification: str = "internal",
        request: RequestContext | None = None,
    ) -> ObjectAccessDecision:
        decision = self._policy.evaluate(
            principal,
            action,
            ResourceContext(
                tenant_id=object_tenant_id,
                resource_type=object_type,
                resource_id=object_id,
                owner_user_id=owner_user_id,
                classification=classification,
            ),
            request or RequestContext(),
        )
        return ObjectAccessDecision(decision.allowed, decision.reason)
