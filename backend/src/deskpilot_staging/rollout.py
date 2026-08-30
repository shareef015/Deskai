from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RolloutObservation:
    ready_replicas: int
    desired_replicas: int
    max_unavailable_observed: int
    error_rate: float
    p95_latency_ms: float


@dataclass(frozen=True, slots=True)
class RolloutPolicy:
    max_unavailable: int = 1
    maximum_error_rate: float = 0.01
    maximum_p95_latency_ms: float = 1500.0


def certify_rollout(observation: RolloutObservation, policy: RolloutPolicy | None = None) -> tuple[bool, tuple[str, ...]]:
    p = policy or RolloutPolicy()
    failures: list[str] = []
    if observation.ready_replicas != observation.desired_replicas:
        failures.append("replicas_not_ready")
    if observation.max_unavailable_observed > p.max_unavailable:
        failures.append("too_many_unavailable")
    if observation.error_rate > p.maximum_error_rate:
        failures.append("error_rate")
    if observation.p95_latency_ms > p.maximum_p95_latency_ms:
        failures.append("latency")
    return (not failures, tuple(failures))
