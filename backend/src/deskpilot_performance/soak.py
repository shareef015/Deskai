from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SoakAssessment:
    memory_growth_mb_per_hour: float
    connection_growth_per_hour: float
    stable: bool
    failures: tuple[str, ...]


def _slope(first: float, last: float, hours: float) -> float:
    if hours <= 0:
        raise ValueError("hours must be positive")
    return (last - first) / hours


def assess_soak(
    *, hours: float, memory_start_mb: float, memory_end_mb: float,
    connections_start: int, connections_end: int,
    max_memory_growth_mb_per_hour: float = 10.0,
    max_connection_growth_per_hour: float = 1.0,
) -> SoakAssessment:
    if min(memory_start_mb, memory_end_mb, connections_start, connections_end) < 0:
        raise ValueError("soak samples cannot be negative")
    memory_growth = _slope(memory_start_mb, memory_end_mb, hours)
    connection_growth = _slope(float(connections_start), float(connections_end), hours)
    failures: list[str] = []
    if memory_growth > max_memory_growth_mb_per_hour:
        failures.append("memory_growth")
    if connection_growth > max_connection_growth_per_hour:
        failures.append("connection_growth")
    return SoakAssessment(memory_growth, connection_growth, not failures, tuple(failures))
