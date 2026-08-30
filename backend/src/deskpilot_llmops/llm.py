from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .costs import CostLedger, UsageRecord
from .models import TraceContext
from .telemetry import TelemetryRecorder


@dataclass(frozen=True, slots=True)
class LlmObservation:
    model_family: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    prompt_fingerprint: str
    response_fingerprint: str


class LlmCallObserver:
    """Records model telemetry without storing raw prompts/responses."""

    def __init__(self, telemetry: TelemetryRecorder, costs: CostLedger) -> None:
        self.telemetry = telemetry
        self.costs = costs

    def record(
        self,
        context: TraceContext,
        *,
        model_family: str,
        prompt: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        started_at: float,
    ) -> LlmObservation:
        usage = UsageRecord(model_family, input_tokens, output_tokens, latency_ms, context.run_id)
        cost = self.costs.add(usage)
        prompt_fp = sha256(prompt.encode("utf-8")).hexdigest()
        response_fp = sha256(response.encode("utf-8")).hexdigest()
        self.telemetry.record_span(
            context,
            name="gen_ai.invoke_model",
            stage="llm",
            started_at=started_at,
            ended_at=started_at + latency_ms / 1000.0,
            attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": model_family,
                "gen_ai.usage.input_tokens": input_tokens,
                "gen_ai.usage.output_tokens": output_tokens,
                "deskpilot.prompt.fingerprint": prompt_fp,
                "deskpilot.response.fingerprint": response_fp,
            },
        )
        self.telemetry.metrics.record("deskpilot.llm.tokens", input_tokens + output_tokens, unit="{token}", labels={"stage": "llm", "model_family": model_family})
        self.telemetry.metrics.record("deskpilot.llm.cost", cost, unit="USD", labels={"stage": "llm", "model_family": model_family})
        return LlmObservation(model_family, input_tokens, output_tokens, latency_ms, cost, prompt_fp, response_fp)
