from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    retrieval_precision: float
    retrieval_recall: float
    groundedness: float
    citation_integrity: float
    route_accuracy: float
    tool_success: float
    hallucination_rate: float
    prompt_injection_block_rate: float
    closure_accuracy: float

    def as_dict(self) -> dict[str, float]:
        return {name: float(getattr(self, name)) for name in self.__dataclass_fields__}


class QualityEvaluator:
    @staticmethod
    def retrieval(*, retrieved: Iterable[str], relevant: Iterable[str]) -> tuple[float, float]:
        got, wanted = set(retrieved), set(relevant)
        if not got:
            return (0.0, 0.0 if wanted else 1.0)
        overlap = len(got & wanted)
        return (overlap / len(got), overlap / len(wanted) if wanted else 1.0)

    @staticmethod
    def bounded_score(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def aggregate(self, rows: Iterable[dict[str, float]]) -> EvaluationResult:
        items = list(rows)
        if not items:
            raise ValueError("evaluation_rows_empty")
        names = EvaluationResult.__dataclass_fields__.keys()
        means = {name: sum(self.bounded_score(row[name]) for row in items) / len(items) for name in names}
        return EvaluationResult(**means)
