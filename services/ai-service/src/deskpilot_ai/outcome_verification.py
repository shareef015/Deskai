from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

Domain = Literal["outlook", "printer", "scanner", "windows", "network"]
TechnicalOutcome = Literal["awaiting_confirmation", "failed", "regression", "inconclusive"]
MAX_CHECKS = 10
MAX_REGRESSION_CHECKS = 5
ALLOWED_CHECKS = frozenset({
    "outlook_connectivity", "outlook_send_receive", "outlook_launch", "outlook_search",
    "print_queue_submission", "physical_test_page", "scanner_detection", "privacy_safe_test_scan",
    "service_state", "resource_baseline", "adapter_state", "dns_resolution", "vpn_connectivity",
    "target_port", "target_business_function",
})


class VerificationError(ValueError):
    pass


@dataclass(frozen=True)
class VerificationContext:
    tenant_id: str
    incident_id: str
    device_id: str
    domain: Domain
    plan_id: str
    plan_provenance_sha256: str
    execution_result_fingerprint: str
    execution_status: str
    rollback_supported: bool
    original_business_function: str


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    check_type: str
    evidence_id: str
    expected_value: str
    observed_value: str
    status: Literal["pass", "fail", "unknown"]
    read_only: bool
    bounded: bool


@dataclass(frozen=True)
class VerificationResult:
    outcome: TechnicalOutcome
    passed_check_ids: tuple[str, ...]
    failed_check_ids: tuple[str, ...]
    unknown_check_ids: tuple[str, ...]
    regression_check_ids: tuple[str, ...]
    employee_confirmation_required: bool
    recovery_route: Literal["employee_confirmation", "rollback", "escalate", "collect_more_evidence"]
    provenance_sha256: str


@dataclass(frozen=True)
class EmployeeConfirmation:
    employee_id: str
    tenant_id: str
    incident_id: str
    device_id: str
    authenticated: bool
    assigned_device: bool
    decision: Literal["confirmed", "not_fixed"]
    verification_provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def evaluate(*, context: VerificationContext, targeted_checks: tuple[CheckResult, ...], regression_checks: tuple[CheckResult, ...]) -> VerificationResult:
    if context.execution_status != "succeeded" or len(context.execution_result_fingerprint) != 64 or len(context.plan_provenance_sha256) != 64:
        raise VerificationError("successful bound execution required")
    if not targeted_checks or len(targeted_checks) > MAX_CHECKS or len(regression_checks) > MAX_REGRESSION_CHECKS:
        raise VerificationError("invalid verification check count")
    all_checks = targeted_checks + regression_checks
    if len({item.check_id for item in all_checks}) != len(all_checks):
        raise VerificationError("duplicate verification check")
    for item in all_checks:
        if item.check_type not in ALLOWED_CHECKS or not item.evidence_id or not item.read_only or not item.bounded:
            raise VerificationError("unsafe or ungrounded verification check")
        if item.status == "pass" and item.observed_value != item.expected_value:
            raise VerificationError("passing check does not meet expectation")
    passed = tuple(sorted(item.check_id for item in targeted_checks if item.status == "pass"))
    failed = tuple(sorted(item.check_id for item in targeted_checks if item.status == "fail"))
    unknown = tuple(sorted(item.check_id for item in targeted_checks if item.status == "unknown"))
    regressions = tuple(sorted(item.check_id for item in regression_checks if item.status != "pass"))
    business_pass = any(item.check_type == "target_business_function" and item.status == "pass" for item in targeted_checks)
    if regressions:
        outcome, route = "regression", "rollback" if context.rollback_supported else "escalate"
    elif failed:
        outcome, route = "failed", "rollback" if context.rollback_supported else "escalate"
    elif unknown or not business_pass:
        outcome, route = "inconclusive", "collect_more_evidence"
    else:
        outcome, route = "awaiting_confirmation", "employee_confirmation"
    payload = {"scope": (context.tenant_id, context.incident_id, context.device_id), "plan": context.plan_id, "execution": context.execution_result_fingerprint, "targeted": [item.__dict__ for item in targeted_checks], "regression": [item.__dict__ for item in regression_checks], "outcome": outcome}
    return VerificationResult(outcome, passed, failed, unknown, regressions, outcome == "awaiting_confirmation", route, _digest(payload))


def validate_employee_confirmation(context: VerificationContext, result: VerificationResult, confirmation: EmployeeConfirmation) -> dict[str, object]:
    if result.outcome != "awaiting_confirmation" or not result.employee_confirmation_required:
        raise VerificationError("technical verification has not passed")
    if not confirmation.authenticated or not confirmation.assigned_device:
        raise VerificationError("authenticated assigned employee required")
    if (confirmation.tenant_id, confirmation.incident_id, confirmation.device_id) != (context.tenant_id, context.incident_id, context.device_id):
        raise VerificationError("employee confirmation scope mismatch")
    if confirmation.verification_provenance_sha256 != result.provenance_sha256:
        raise VerificationError("confirmation does not match verification result")
    phase = "resolved" if confirmation.decision == "confirmed" else "verification"
    return {"phase": phase, "verification_status": "verified" if confirmation.decision == "confirmed" else "employee_reports_not_fixed", "employee_confirmation_actor_id": confirmation.employee_id, "verification_provenance_sha256": result.provenance_sha256, "final_status": "resolved" if phase == "resolved" else None}


def supervisor_handoff(result: VerificationResult) -> dict[str, object]:
    phase = "confirmation" if result.recovery_route == "employee_confirmation" else "execution" if result.recovery_route == "rollback" else "diagnosis" if result.recovery_route == "collect_more_evidence" else "escalated"
    return {"phase": phase, "verification_status": result.outcome, "verification_recovery_route": result.recovery_route, "verification_provenance_sha256": result.provenance_sha256, "regression_check_ids": result.regression_check_ids}
