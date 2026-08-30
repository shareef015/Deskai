from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CanaryPolicy:
    maximum_error_rate: float = 0.01
    maximum_p95_latency_ms: float = 1500.0
    maximum_saturation: float = 0.80
    minimum_golden_pass_rate: float = 1.0
    minimum_groundedness: float = 0.95


@dataclass(frozen=True, slots=True)
class CanaryObservation:
    error_rate: float
    p95_latency_ms: float
    saturation: float
    golden_pass_rate: float
    groundedness: float


def certify_canary(observation: CanaryObservation, policy: CanaryPolicy | None = None) -> tuple[bool, tuple[str, ...]]:
    p = policy or CanaryPolicy()
    failures: list[str] = []
    if observation.error_rate > p.maximum_error_rate:
        failures.append("error_rate")
    if observation.p95_latency_ms > p.maximum_p95_latency_ms:
        failures.append("latency")
    if observation.saturation > p.maximum_saturation:
        failures.append("saturation")
    if observation.golden_pass_rate < p.minimum_golden_pass_rate:
        failures.append("golden_regression")
    if observation.groundedness < p.minimum_groundedness:
        failures.append("groundedness_regression")
    return (not failures, tuple(failures))
