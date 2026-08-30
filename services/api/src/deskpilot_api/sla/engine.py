from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .calendar import BusinessCalendar

TARGETS = {
    1: ("continuous", 15, 240, 5),
    2: ("business", 30, 480, 15),
    3: ("business", 120, 1440, 30),
    4: ("business", 240, 2400, 60),
    5: ("business", 480, 4800, 240),
}


@dataclass(frozen=True, slots=True)
class SlaDecision:
    priority: int
    policy_version: str
    acknowledgement_due_at: datetime
    resolution_due_at: datetime
    unowned_escalation_at: datetime


def calculate_sla(priority: int, opened_at: datetime, calendar: BusinessCalendar) -> SlaDecision:
    if priority not in TARGETS or opened_at.tzinfo is None:
        raise ValueError("valid priority and aware opening time are required")
    calendar_type, acknowledge, resolve, unowned = TARGETS[priority]
    add = (lambda value: opened_at + timedelta(minutes=value)) if calendar_type == "continuous" else (lambda value: calendar.add_minutes(opened_at, value))
    return SlaDecision(priority, "sla-v1", add(acknowledge), add(resolve), add(unowned))


def utilization_percent(started_at: datetime, due_at: datetime, now: datetime, paused_seconds: int = 0) -> float:
    budget = max((due_at - started_at).total_seconds(), 1)
    consumed = max((now - started_at).total_seconds() - max(paused_seconds, 0), 0)
    return round(consumed / budget * 100, 2)


def escalation_level(utilization: float, *, has_owner: bool, unowned_due: bool) -> str | None:
    if not has_owner and unowned_due: return "unowned"
    if utilization >= 100: return "breached"
    if utilization >= 80: return "warning"
    return None
