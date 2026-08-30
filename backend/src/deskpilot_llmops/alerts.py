from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AlertRule:
    name: str
    metric: str
    comparator: str
    threshold: float
    severity: str


@dataclass(frozen=True, slots=True)
class Alert:
    rule: str
    metric: str
    value: float
    threshold: float
    severity: str


class AlertEngine:
    def __init__(self, rules: list[AlertRule]) -> None:
        self.rules = tuple(rules)

    def evaluate(self, metrics: dict[str, float]) -> tuple[Alert, ...]:
        alerts: list[Alert] = []
        for rule in self.rules:
            if rule.metric not in metrics:
                continue
            value = metrics[rule.metric]
            fired = (rule.comparator == "lt" and value < rule.threshold) or (rule.comparator == "gt" and value > rule.threshold)
            if rule.comparator not in {"lt", "gt"}:
                raise ValueError("unsupported_alert_comparator")
            if fired:
                alerts.append(Alert(rule.name, rule.metric, value, rule.threshold, rule.severity))
        return tuple(alerts)
