from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueAssessment:
    arrival_rate: float
    service_rate: float
    utilization: float
    stable: bool
    net_backlog_per_second: float
    drain_seconds: float | None


def assess_queue(*, arrival_rate: float, service_rate: float, backlog: int = 0) -> QueueAssessment:
    if arrival_rate < 0 or service_rate <= 0 or backlog < 0:
        raise ValueError("invalid queue parameters")
    utilization = arrival_rate / service_rate
    stable = arrival_rate < service_rate
    net = max(0.0, arrival_rate - service_rate)
    drain = None if not stable else backlog / (service_rate - arrival_rate) if backlog else 0.0
    return QueueAssessment(arrival_rate, service_rate, utilization, stable, net, drain)
