from __future__ import annotations

from dataclasses import dataclass

TRANSITIONS: dict[str, frozenset[str]] = {
    "new": frozenset({"triaging", "cancelled"}),
    "triaging": frozenset({"awaiting_consent", "investigating", "escalated", "cancelled"}),
    "awaiting_consent": frozenset({"investigating", "escalated", "cancelled"}),
    "investigating": frozenset({"awaiting_approval", "verifying", "escalated", "cancelled"}),
    "awaiting_approval": frozenset({"remediating", "escalated", "cancelled"}),
    "remediating": frozenset({"verifying", "escalated"}),
    "verifying": frozenset({"resolved", "investigating", "remediating", "escalated"}),
    "escalated": frozenset({"investigating", "cancelled"}),
    "resolved": frozenset(),
    "cancelled": frozenset(),
}

GUARDS: dict[tuple[str, str], frozenset[str]] = {
    ("awaiting_consent", "investigating"): frozenset({"diagnostic_consent_valid", "device_relationship_valid"}),
    ("awaiting_approval", "remediating"): frozenset({"action_approval_valid", "plan_fingerprint_matches", "pre_state_captured"}),
    ("remediating", "verifying"): frozenset({"remediation_execution_complete"}),
    ("verifying", "resolved"): frozenset({"technical_verification_passed", "employee_confirmation_received", "audit_events_complete"}),
}


@dataclass(frozen=True, slots=True)
class TransitionDecision:
    allowed: bool
    reason_code: str
    missing_guards: frozenset[str] = frozenset()


def decide_transition(current: str, target: str, satisfied_guards: frozenset[str]) -> TransitionDecision:
    if target not in TRANSITIONS.get(current, frozenset()):
        return TransitionDecision(False, "transition_not_allowed")
    required = set(GUARDS.get((current, target), frozenset()))
    if target == "escalated":
        required.add("escalation_reason_recorded")
    missing = frozenset(required - satisfied_guards)
    if missing:
        return TransitionDecision(False, "transition_guard_failed", missing)
    return TransitionDecision(True, "transition_allowed")
