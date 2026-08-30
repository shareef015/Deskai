from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


_ALLOWED_LABEL_KEYS = frozenset({"domain", "stage", "status", "tool", "model_family", "evaluator", "environment"})


@dataclass(frozen=True, slots=True)
class MetricSample:
    name: str
    value: float
    unit: str
    labels: tuple[tuple[str, str], ...]


class MetricRegistry:
    def __init__(self) -> None:
        self._samples: list[MetricSample] = []

    def record(self, name: str, value: float, *, unit: str = "1", labels: dict[str, str] | None = None) -> None:
        if not name.startswith("deskpilot."):
            raise ValueError("metric_name_must_be_namespaced")
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("metric_value_must_be_finite")
        labels = labels or {}
        unknown = set(labels) - _ALLOWED_LABEL_KEYS
        if unknown:
            raise ValueError(f"high_cardinality_or_unknown_metric_labels:{','.join(sorted(unknown))}")
        self._samples.append(MetricSample(name, float(value), unit, tuple(sorted(labels.items()))))

    def samples(self, name: str | None = None) -> tuple[MetricSample, ...]:
        rows: Iterable[MetricSample] = self._samples
        if name is not None:
            rows = (row for row in rows if row.name == name)
        return tuple(rows)

    def latest(self, name: str) -> float | None:
        rows = self.samples(name)
        return rows[-1].value if rows else None
