from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

Severity = Literal["warning", "blocking", "critical"]
Outcome = Literal["pass", "revise", "escalate"]
MAX_ACTIONS = 4
MAX_FINDINGS = 20
REQUIRED_VERIFICATION = frozenset({"technical_state_verified", "target_business_function_works", "employee_confirms"})
PROHIBITED_CAPABILITIES = frozenset({
    "disable_firewall", "disable_endpoint_security", "collect_credentials", "collect_private_key",
    "bypass_enterprise_policy", "delete_user_data", "wipe_device", "unrestricted_shell",
})


class RemediationCriticError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewContext:
    tenant_id: str
    incident_id: str
    device_id: str
    root_cause: str
    fusion_provenance_sha256: str
    plan_id: str
    plan_provenance_sha256: str
    plan_author_id: str
    approval_requester_id: str


@dataclass(frozen=True)
class ReviewAction:
    action_id: str
    capability: str
    risk: Literal["low", "medium", "high"]
    blast_radius: Literal["process", "user", "device", "shared_service", "tenant"]
    evidence_ids: tuple[str, ...]
    prerequisites: tuple[str, ...]
    persistent_change: bool
    pre_state_fields: tuple[str, ...]
    rollback_action: str | None
    required_approver: str
    proposed_approver_id: str | None
    verification: tuple[str, ...]
    idempotency_key: str


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    action_id: str | None
    message: str


@dataclass(frozen=True)
class CriticResult:
    outcome: Outcome
    findings: tuple[Finding, ...]
    reviewed_plan_id: str
    reason: str
    provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def _finding(code: str, severity: Severity, action_id: str | None, message: str) -> Finding:
    return Finding(code, severity, action_id, message)


def review_plan(context: ReviewContext, actions: tuple[ReviewAction, ...], allowed_capabilities: frozenset[str]) -> CriticResult:
    if not all((context.tenant_id, context.incident_id, context.device_id, context.root_cause, context.plan_id)):
        raise RemediationCriticError("review scope incomplete")
    if len(context.fusion_provenance_sha256) != 64 or len(context.plan_provenance_sha256) != 64:
        raise RemediationCriticError("review provenance incomplete")
    if not actions or len(actions) > MAX_ACTIONS:
        raise RemediationCriticError("invalid plan action count")
    findings: list[Finding] = []
    action_ids = [item.action_id for item in actions]
    idempotency_keys = [item.idempotency_key for item in actions]
    if len(action_ids) != len(set(action_ids)):
        findings.append(_finding("duplicate_action", "blocking", None, "Action identifiers must be unique."))
    if len(idempotency_keys) != len(set(idempotency_keys)) or any(not key for key in idempotency_keys):
        findings.append(_finding("invalid_idempotency", "blocking", None, "Every action needs a unique idempotency key."))
    if context.plan_author_id == context.approval_requester_id:
        findings.append(_finding("requester_author_conflict", "blocking", None, "Plan author cannot request its approval."))
    for action in actions:
        if action.capability in PROHIBITED_CAPABILITIES:
            findings.append(_finding("prohibited_capability", "critical", action.action_id, "Capability is prohibited by policy."))
        elif action.capability not in allowed_capabilities:
            findings.append(_finding("unsupported_capability", "blocking", action.action_id, "Capability is outside the governed allowlist."))
        if not action.evidence_ids:
            findings.append(_finding("missing_evidence_link", "blocking", action.action_id, "Action is not linked to root-cause evidence."))
        if not action.prerequisites:
            findings.append(_finding("missing_prerequisites", "blocking", action.action_id, "Action prerequisites are missing."))
        if action.blast_radius in {"shared_service", "tenant"} and action.risk != "high":
            findings.append(_finding("risk_underclassified", "critical", action.action_id, "Shared blast radius must be high risk."))
        if action.persistent_change and (not action.pre_state_fields or not action.rollback_action):
            findings.append(_finding("rollback_gap", "blocking", action.action_id, "Persistent change lacks pre-state or rollback."))
        if not REQUIRED_VERIFICATION <= set(action.verification):
            findings.append(_finding("verification_gap", "blocking", action.action_id, "Technical, business, and employee verification are required."))
        if not action.required_approver:
            findings.append(_finding("approval_role_missing", "blocking", action.action_id, "Qualified approval role is missing."))
        if action.proposed_approver_id and action.proposed_approver_id in {context.plan_author_id, context.approval_requester_id}:
            findings.append(_finding("segregation_of_duties", "critical", action.action_id, "Approver must be independent of author and requester."))
    findings = sorted(findings, key=lambda item: ({"critical": 0, "blocking": 1, "warning": 2}[item.severity], item.code, item.action_id or ""))[:MAX_FINDINGS]
    outcome: Outcome = "escalate" if any(item.severity == "critical" for item in findings) else "revise" if findings else "pass"
    reason = "critical_policy_violation" if outcome == "escalate" else "plan_revision_required" if outcome == "revise" else "independent_review_passed"
    payload = {"scope": (context.tenant_id, context.incident_id, context.device_id), "plan_id": context.plan_id, "plan_provenance": context.plan_provenance_sha256, "findings": [item.__dict__ for item in findings], "outcome": outcome}
    return CriticResult(outcome, tuple(findings), context.plan_id, reason, _digest(payload))


def supervisor_handoff(result: CriticResult) -> dict[str, object]:
    phase = "approval" if result.outcome == "pass" else "remediation_planning" if result.outcome == "revise" else "escalated"
    return {"phase": phase, "remediation_critic_status": result.outcome, "remediation_critic_findings": tuple(item.__dict__ for item in result.findings), "reviewed_plan_id": result.reviewed_plan_id, "remediation_critic_provenance_sha256": result.provenance_sha256}
