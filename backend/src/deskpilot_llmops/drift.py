from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DriftFinding:
    metric: str
    baseline: float
    current: float
    delta: float
    degraded: bool


class DriftDetector:
    def __init__(self, *, maximum_relative_drop: float = 0.05, maximum_absolute_increase: float = 0.02) -> None:
        self.maximum_relative_drop = maximum_relative_drop
        self.maximum_absolute_increase = maximum_absolute_increase

    def quality(self, metric: str, baseline: float, current: float) -> DriftFinding:
        allowed = baseline * self.maximum_relative_drop
        delta = current - baseline
        return DriftFinding(metric, baseline, current, delta, delta < -allowed)

    def risk(self, metric: str, baseline: float, current: float) -> DriftFinding:
        delta = current - baseline
        return DriftFinding(metric, baseline, current, delta, delta > self.maximum_absolute_increase)
