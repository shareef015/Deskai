from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import SpanRecord


@dataclass(frozen=True, slots=True)
class OTelSpanEnvelope:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    attributes: Mapping[str, object]


def to_otel_envelope(span: SpanRecord) -> OTelSpanEnvelope:
    attrs: dict[str, object] = {
        "service.name": "deskpilot-ai",
        "deskpilot.stage": span.stage,
        "deskpilot.status": span.status,
        **dict(span.attributes),
    }
    operation_by_stage = {
        "rag": "retrieval",
        "langgraph": "invoke_workflow",
        "llm": "chat",
        "mcp": "execute_tool",
        "remediation": "execute_tool",
    }
    if span.stage in operation_by_stage:
        attrs.setdefault("gen_ai.operation.name", operation_by_stage[span.stage])
    return OTelSpanEnvelope(span.name, span.trace_id, span.span_id, span.parent_span_id, attrs)


def langsmith_trace_metadata(*, tenant_id: str, correlation_id: str, environment: str, release: str) -> dict[str, object]:
    # `tenant_id` is deliberately projected as an opaque scope value. Deployments may hash it before export.
    return {
        "metadata": {
            "tenant_hash_scope": tenant_id,
            "correlation_id": correlation_id,
            "environment": environment,
            "release": release,
        },
        "tags": ["deskpilot", "quality", environment],
    }
