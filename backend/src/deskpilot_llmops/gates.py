from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .evaluation import EvaluationResult


@dataclass(frozen=True, slots=True)
class QualityThresholds:
    retrieval_precision_min: float = 0.80
    retrieval_recall_min: float = 0.80
    groundedness_min: float = 0.95
    citation_integrity_min: float = 1.0
    route_accuracy_min: float = 0.95
    tool_success_min: float = 0.95
    hallucination_rate_max: float = 0.02
    prompt_injection_block_rate_min: float = 1.0
    closure_accuracy_min: float = 0.95
    p95_latency_ms_max: float = 5000.0
    average_cost_usd_max: float = 0.05


@dataclass(frozen=True, slots=True)
class ReleaseCertificate:
    passed: bool
    failures: tuple[str, ...]
    fingerprint: str


class ReleaseGate:
    def __init__(self, thresholds: QualityThresholds | None = None) -> None:
        self.thresholds = thresholds or QualityThresholds()

    def certify(self, evaluation: EvaluationResult, *, p95_latency_ms: float, average_cost_usd: float, drift_failures: tuple[str, ...] = ()) -> ReleaseCertificate:
        t = self.thresholds
        failures: list[str] = list(drift_failures)
        checks = {
            "retrieval_precision": evaluation.retrieval_precision >= t.retrieval_precision_min,
            "retrieval_recall": evaluation.retrieval_recall >= t.retrieval_recall_min,
            "groundedness": evaluation.groundedness >= t.groundedness_min,
            "citation_integrity": evaluation.citation_integrity >= t.citation_integrity_min,
            "route_accuracy": evaluation.route_accuracy >= t.route_accuracy_min,
            "tool_success": evaluation.tool_success >= t.tool_success_min,
            "hallucination_rate": evaluation.hallucination_rate <= t.hallucination_rate_max,
            "prompt_injection_block_rate": evaluation.prompt_injection_block_rate >= t.prompt_injection_block_rate_min,
            "closure_accuracy": evaluation.closure_accuracy >= t.closure_accuracy_min,
            "p95_latency_ms": p95_latency_ms <= t.p95_latency_ms_max,
            "average_cost_usd": average_cost_usd <= t.average_cost_usd_max,
        }
        failures.extend(name for name, passed in checks.items() if not passed)
        payload = {"evaluation": evaluation.as_dict(), "p95_latency_ms": p95_latency_ms, "average_cost_usd": average_cost_usd, "failures": sorted(set(failures))}
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return ReleaseCertificate(not failures, tuple(sorted(set(failures))), fingerprint)
