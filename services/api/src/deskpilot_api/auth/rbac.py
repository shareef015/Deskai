from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    scope_type: str
    scope_id: UUID | None
    valid_from: datetime
    valid_until: datetime | None
    revoked_at: datetime | None = None

    def active_at(self, now: datetime) -> bool:
        return (
            self.valid_from <= now
            and (self.valid_until is None or now < self.valid_until)
            and self.revoked_at is None
        )


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    tenant_id: UUID
    actor_id: UUID
    action: str
    resource_type: str
    resource_id: UUID
    owner_id: UUID | None = None
    proposer_id: UUID | None = None
    risk_level: str | None = None


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason_code: str
    matched_assignment_ids: tuple[UUID, ...] = ()


class PolicyEngine:
    def __init__(self, roles: dict[str, dict[str, frozenset[str]]]) -> None:
        self._roles = roles

    def decide(
        self,
        request: AuthorizationRequest,
        assignments: tuple[RoleAssignment, ...],
        *,
        now: datetime | None = None,
    ) -> AuthorizationDecision:
        instant = now or datetime.now(UTC)
        applicable = tuple(
            assignment
            for assignment in assignments
            if assignment.tenant_id == request.tenant_id
            and assignment.user_id == request.actor_id
            and assignment.active_at(instant)
            and _scope_matches(assignment, request)
        )
        if request.proposer_id == request.actor_id and request.action.startswith("remediation.approve"):
            return AuthorizationDecision(False, "segregation_of_duties_proposer")
        if (
            request.owner_id == request.actor_id
            and request.risk_level in {"medium", "high"}
            and request.action.startswith("remediation.approve")
        ):
            return AuthorizationDecision(False, "segregation_of_duties_requester")
        if any(request.action in self._roles.get(item.role, {}).get("deny", frozenset()) for item in applicable):
            return AuthorizationDecision(False, "explicit_deny")
        allowed = tuple(
            item.id
            for item in applicable
            if request.action in self._roles.get(item.role, {}).get("allow", frozenset())
        )
        if not allowed:
            return AuthorizationDecision(False, "no_matching_allow")
        return AuthorizationDecision(True, "allowed", allowed)


def _scope_matches(assignment: RoleAssignment, request: AuthorizationRequest) -> bool:
    if assignment.scope_type == "tenant":
        return assignment.scope_id is None or assignment.scope_id == request.tenant_id
    if assignment.scope_type in {"incident", "device"}:
        return assignment.scope_type == request.resource_type and assignment.scope_id == request.resource_id
    return assignment.scope_id is not None
