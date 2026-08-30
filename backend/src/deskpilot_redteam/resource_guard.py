from __future__ import annotations

from dataclasses import dataclass


class ResourceAbuseViolation(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ModelBudget:
    max_input_chars: int = 24_000
    max_output_tokens: int = 4_096
    max_model_calls: int = 8
    max_tool_calls: int = 12
    max_wall_seconds: float = 120.0


@dataclass(slots=True)
class ResourceLedger:
    model_calls: int = 0
    tool_calls: int = 0
    output_tokens: int = 0


class ModelResourceGuard:
    def __init__(self, budget: ModelBudget | None = None) -> None:
        self.budget = budget or ModelBudget()

    def validate_input(self, text: str) -> None:
        if len(text) > self.budget.max_input_chars:
            raise ResourceAbuseViolation("input_budget_exceeded")

    def record_model_call(self, ledger: ResourceLedger, *, output_tokens: int) -> None:
        if output_tokens < 0:
            raise ValueError("invalid_output_tokens")
        ledger.model_calls += 1
        ledger.output_tokens += output_tokens
        if ledger.model_calls > self.budget.max_model_calls:
            raise ResourceAbuseViolation("model_call_budget_exceeded")
        if ledger.output_tokens > self.budget.max_output_tokens:
            raise ResourceAbuseViolation("output_token_budget_exceeded")

    def record_tool_call(self, ledger: ResourceLedger) -> None:
        ledger.tool_calls += 1
        if ledger.tool_calls > self.budget.max_tool_calls:
            raise ResourceAbuseViolation("tool_call_budget_exceeded")

    def validate_elapsed(self, *, started_at: float, now: float) -> None:
        if now - started_at >= self.budget.max_wall_seconds:
            raise ResourceAbuseViolation("wall_time_budget_exceeded")
