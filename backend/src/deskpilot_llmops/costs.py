from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPriceProfile:
    model_family: str
    input_per_million_usd: float
    output_per_million_usd: float


@dataclass(frozen=True, slots=True)
class UsageRecord:
    model_family: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    run_id: str


class CostLedger:
    def __init__(self, profiles: list[ModelPriceProfile]) -> None:
        self._profiles = {p.model_family: p for p in profiles}
        self._records: list[UsageRecord] = []

    def add(self, record: UsageRecord) -> float:
        if record.input_tokens < 0 or record.output_tokens < 0 or record.latency_ms < 0:
            raise ValueError("usage_values_must_be_non_negative")
        profile = self._profiles.get(record.model_family)
        if profile is None:
            raise KeyError("unknown_model_price_profile")
        self._records.append(record)
        return ((record.input_tokens * profile.input_per_million_usd) + (record.output_tokens * profile.output_per_million_usd)) / 1_000_000

    def total_usd(self) -> float:
        total = 0.0
        for row in self._records:
            p = self._profiles[row.model_family]
            total += ((row.input_tokens * p.input_per_million_usd) + (row.output_tokens * p.output_per_million_usd)) / 1_000_000
        return total

    def total_tokens(self) -> int:
        return sum(r.input_tokens + r.output_tokens for r in self._records)
