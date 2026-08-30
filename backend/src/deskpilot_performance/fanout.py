from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FanoutAssessment:
    active_connections: int
    maximum_connections: int
    utilization: float
    headroom: int
    safe: bool


def assess_fanout(*, active_connections: int, maximum_connections: int, safe_utilization: float = 0.8) -> FanoutAssessment:
    if active_connections < 0 or maximum_connections <= 0 or active_connections > maximum_connections:
        raise ValueError("invalid fanout sample")
    if not 0 < safe_utilization <= 1:
        raise ValueError("invalid safe utilization")
    utilization = active_connections / maximum_connections
    return FanoutAssessment(active_connections, maximum_connections, utilization, maximum_connections - active_connections, utilization <= safe_utilization)
