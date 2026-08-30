from __future__ import annotations

from dataclasses import dataclass

POLICY_VERSION = "priority-v1"


@dataclass(frozen=True, slots=True)
class PrioritySignals:
    impact_score: int
    urgency_score: int
    affected_user_count: int = 1
    business_critical_service: bool = False
    security_or_safety_risk: bool = False
    complete_site_outage: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.impact_score <= 5 or not 1 <= self.urgency_score <= 5:
            raise ValueError("impact and urgency must be between 1 and 5")
        if not 1 <= self.affected_user_count <= 100_000:
            raise ValueError("affected user count is outside policy bounds")


@dataclass(frozen=True, slots=True)
class PriorityDecision:
    priority: int
    severity: str
    impact_score: int
    urgency_score: int
    policy_version: str
    reason_codes: tuple[str, ...]


def classify_priority(signals: PrioritySignals) -> PriorityDecision:
    reasons: list[str] = []
    if signals.security_or_safety_risk:
        reasons.append("security_or_safety_risk")
    if signals.complete_site_outage:
        reasons.append("complete_site_outage")
    if reasons:
        return PriorityDecision(1, "sev1", signals.impact_score, signals.urgency_score, POLICY_VERSION, tuple(reasons))
    score = signals.impact_score + signals.urgency_score
    if signals.affected_user_count >= 100 and signals.business_critical_service:
        score = max(score, 7)
        reasons.append("verified_widespread_critical_impact")
    matrix = ((9, 1, "sev1"), (7, 2, "sev2"), (5, 3, "sev3"), (3, 4, "sev4"), (2, 5, "sev5"))
    priority, severity = next((priority, severity) for minimum, priority, severity in matrix if score >= minimum)
    reasons.append(f"impact_urgency_score_{score}")
    return PriorityDecision(priority, severity, signals.impact_score, signals.urgency_score, POLICY_VERSION, tuple(reasons))
