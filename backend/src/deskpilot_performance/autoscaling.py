from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True, slots=True)
class ScaleDecision:
    current_replicas: int
    desired_replicas: int
    reason: str


def desired_replicas(
    *, current_replicas: int, observed_utilization: float, target_utilization: float,
    minimum: int, maximum: int, max_scale_up_factor: float = 2.0
) -> ScaleDecision:
    if current_replicas <= 0 or minimum <= 0 or maximum < minimum:
        raise ValueError("invalid replica limits")
    if not 0 < target_utilization <= 1 or observed_utilization < 0:
        raise ValueError("invalid utilization")
    raw = ceil(current_replicas * observed_utilization / target_utilization)
    capped_up = min(raw, max(current_replicas, ceil(current_replicas * max_scale_up_factor)))
    desired = min(max(capped_up, minimum), maximum)
    if desired > current_replicas:
        reason = "scale_up"
    elif desired < current_replicas:
        reason = "scale_down"
    else:
        reason = "hold"
    return ScaleDecision(current_replicas, desired, reason)
