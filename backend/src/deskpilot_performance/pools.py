from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PoolPressure:
    active: int
    maximum: int
    waiting: int
    utilization: float
    saturated: bool


def assess_pool(*, active: int, maximum: int, waiting: int, saturation_threshold: float = 0.8) -> PoolPressure:
    if active < 0 or maximum <= 0 or waiting < 0 or active > maximum:
        raise ValueError("invalid pool sample")
    utilization = active / maximum
    return PoolPressure(active, maximum, waiting, utilization, utilization >= saturation_threshold or waiting > 0)
