from __future__ import annotations

from dataclasses import dataclass
from secrets import token_urlsafe

from .models import ApprovalGrant, RemediationPlan, RunContext


class ApprovalError(RuntimeError):
    pass


@dataclass(slots=True)
class _ApprovalRecord:
    grant: ApprovalGrant
    consumed: bool = False


class ApprovalGate:
    def __init__(self) -> None:
        self._records: dict[str, _ApprovalRecord] = {}

    def issue(self, context: RunContext, plan: RemediationPlan, *, now: float, ttl_seconds: float = 300) -> ApprovalGrant:
        context.require_capability("remediation:approve")
        grant = ApprovalGrant(
            approval_id=token_urlsafe(18),
            tenant_id=context.tenant_id,
            session_id=context.session_id,
            user_id=context.user_id,
            plan_fingerprint=plan.fingerprint,
            issued_at=now,
            expires_at=now + ttl_seconds,
        )
        self._records[grant.approval_id] = _ApprovalRecord(grant)
        return grant

    def consume(self, context: RunContext, plan: RemediationPlan, approval_id: str, *, now: float) -> ApprovalGrant:
        record = self._records.get(approval_id)
        if record is None:
            raise ApprovalError("approval_not_found")
        grant = record.grant
        if record.consumed:
            raise ApprovalError("approval_already_consumed")
        if grant.expires_at <= now:
            raise ApprovalError("approval_expired")
        if grant.tenant_id != context.tenant_id or grant.session_id != context.session_id:
            raise ApprovalError("approval_context_mismatch")
        if grant.plan_fingerprint != plan.fingerprint:
            raise ApprovalError("approval_plan_mismatch")
        record.consumed = True
        return grant
