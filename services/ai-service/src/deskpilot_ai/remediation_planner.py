from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

Risk = Literal["low", "medium", "high", "prohibited"]
MAX_ACTIONS = 4
MAX_CANDIDATES = 8
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "prohibited": 3}
QUALIFIED_APPROVERS = {
    "low": {"service_desk_lead", "endpoint_administrator"},
    "medium": {"endpoint_administrator", "network_administrator", "messaging_administrator"},
    "high": {"security_administrator", "identity_administrator", "network_administrator", "messaging_administrator"},
}
PROHIBITED_ACTIONS = frozenset({
    "disable_firewall", "disable_endpoint_security", "collect_credentials", "collect_private_key",
    "bypass_enterprise_policy", "delete_user_data", "wipe_device", "unrestricted_shell",
})


class RemediationPlanningError(ValueError):
    pass


@dataclass(frozen=True)
class RootCauseContext:
    tenant_id: str
    incident_id: str
    device_id: str
    root_cause: str
    fusion_status: str
    fusion_provenance_sha256: str
    evidence_ids: tuple[str, ...]
    target_business_function: str


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    capability: str
    risk: Risk
    blast_radius: Literal["process", "user", "device", "shared_service", "tenant"]
    prerequisites: tuple[str, ...]
    expected_effect: str
    persistent_change: bool
    pre_state_fields: tuple[str, ...]
    rollback_action: str | None
    required_approver: str
    verification: tuple[str, ...]
    idempotency_key: str
    rank: int


@dataclass(frozen=True)
class RemediationPlan:
    plan_id: str
    root_cause: str
    actions: tuple[ActionCandidate, ...]
    maximum_risk: Literal["low", "medium", "high"]
    required_approvers: tuple[str, ...]
    outcome: Literal["approval_required", "escalate"]
    reason: str
    provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def _validate_context(context: RootCauseContext) -> None:
    if context.fusion_status != "root_cause_ready" or not context.root_cause or not context.evidence_ids:
        raise RemediationPlanningError("grounded root cause required")
    if len(context.fusion_provenance_sha256) != 64:
        raise RemediationPlanningError("fusion provenance required")
    if not all((context.tenant_id, context.incident_id, context.device_id, context.target_business_function)):
        raise RemediationPlanningError("scope incomplete")


def _validate_action(action: ActionCandidate) -> None:
    if action.capability in PROHIBITED_ACTIONS or action.risk == "prohibited":
        raise RemediationPlanningError("prohibited remediation")
    if not action.action_id or not action.capability or not action.expected_effect or not action.idempotency_key:
        raise RemediationPlanningError("action contract incomplete")
    required_verification = {"technical_state_verified", "target_business_function_works", "employee_confirms"}
    if not required_verification <= set(action.verification):
        raise RemediationPlanningError("end-to-end verification required")
    if action.persistent_change and (not action.pre_state_fields or not action.rollback_action):
        raise RemediationPlanningError("persistent change requires pre-state and rollback")
    if action.required_approver not in QUALIFIED_APPROVERS[action.risk]:
        raise RemediationPlanningError("unqualified approver")
    if action.blast_radius in {"shared_service", "tenant"} and action.risk != "high":
        raise RemediationPlanningError("shared blast radius must be high risk")


def build_plan(context: RootCauseContext, candidates: tuple[ActionCandidate, ...]) -> RemediationPlan:
    _validate_context(context)
    if not candidates or len(candidates) > MAX_CANDIDATES:
        raise RemediationPlanningError("invalid action candidates")
    for item in candidates:
        _validate_action(item)
    if len({item.action_id for item in candidates}) != len(candidates) or len({item.idempotency_key for item in candidates}) != len(candidates):
        raise RemediationPlanningError("duplicate action or idempotency key")
    ordered = sorted(candidates, key=lambda item: (RISK_ORDER[item.risk], item.rank, item.action_id))
    minimum_risk = ordered[0].risk
    minimal = tuple(item for item in ordered if item.risk == minimum_risk)[:MAX_ACTIONS]
    if not minimal:
        raise RemediationPlanningError("no safe minimal plan")
    maximum_risk = max((item.risk for item in minimal), key=RISK_ORDER.__getitem__)
    payload = {"scope": (context.tenant_id, context.incident_id, context.device_id), "root_cause": context.root_cause, "fusion": context.fusion_provenance_sha256, "actions": [item.__dict__ for item in minimal]}
    provenance = _digest(payload)
    return RemediationPlan("rmp-" + provenance[:20], context.root_cause, minimal, maximum_risk, tuple(sorted({item.required_approver for item in minimal})), "approval_required", "least_risk_minimal_change", provenance)


def supervisor_handoff(plan: RemediationPlan) -> dict[str, object]:
    return {"phase": "approval", "remediation_plan_id": plan.plan_id, "remediation_plan_status": plan.outcome, "remediation_maximum_risk": plan.maximum_risk, "required_approvers": plan.required_approvers, "remediation_plan_provenance_sha256": plan.provenance_sha256, "planned_actions": tuple(item.action_id for item in plan.actions)}
