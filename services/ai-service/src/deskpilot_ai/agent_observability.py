from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Literal

EventType = Literal["graph_transition", "agent_decision", "retrieval", "tool_call", "human_decision", "retry", "error", "budget", "terminal"]
MAX_EVENTS_PER_TRACE = 500
MAX_ATTRIBUTE_KEYS = 20
MAX_ATTRIBUTE_VALUE_CHARS = 256
ALLOWED_ATTRIBUTES = frozenset({
    "from_phase", "to_phase", "route_reason", "agent_id", "decision", "outcome", "evidence_ids",
    "model_id", "prompt_version", "config_fingerprint", "retrieval_round", "retrieval_count",
    "tool_id", "capability_id", "status", "error_class", "retry_count", "actor_role",
    "tokens", "cost_microusd", "latency_ms", "budget_remaining", "audit_event_id",
})
SECRET_PATTERN = re.compile(r"(?i)(password|token|secret|api[_-]?key|authorization)\s*[:=]\s*\S+")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


class TraceError(ValueError):
    pass


@dataclass(frozen=True)
class TraceScope:
    trace_id: str
    tenant_id: str
    incident_id: str
    thread_id: str
    correlation_id: str


@dataclass(frozen=True)
class TraceEvent:
    sequence: int
    event_id: str
    event_type: EventType
    scope: TraceScope
    timestamp: str
    attributes: dict[str, object]
    input_fingerprint: str | None
    output_fingerprint: str | None
    audit_event_id: str | None
    previous_event_sha256: str
    event_sha256: str


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()


def _safe_value(value: object) -> object:
    if isinstance(value, str):
        return EMAIL_PATTERN.sub("[redacted-email]", SECRET_PATTERN.sub("[redacted-secret]", value))[:MAX_ATTRIBUTE_VALUE_CHARS]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return tuple(_safe_value(item) for item in value[:20])
    raise TraceError("unsupported trace attribute value")


def append_event(*, existing: tuple[TraceEvent, ...], scope: TraceScope, event_type: EventType, timestamp: str, attributes: dict[str, object], input_fingerprint: str | None = None, output_fingerprint: str | None = None, audit_event_id: str | None = None) -> TraceEvent:
    if len(existing) >= MAX_EVENTS_PER_TRACE or not all((scope.trace_id, scope.tenant_id, scope.incident_id, scope.thread_id, scope.correlation_id)):
        raise TraceError("invalid trace scope or event limit")
    if any(item.scope != scope for item in existing):
        raise TraceError("cross-scope trace event")
    if len(attributes) > MAX_ATTRIBUTE_KEYS or not set(attributes) <= ALLOWED_ATTRIBUTES:
        raise TraceError("trace attribute not allowed")
    if event_type in {"agent_decision", "tool_call", "human_decision", "terminal"} and not output_fingerprint:
        raise TraceError("decision event requires output fingerprint")
    for fingerprint in (input_fingerprint, output_fingerprint):
        if fingerprint is not None and len(fingerprint) != 64:
            raise TraceError("invalid content fingerprint")
    safe = {key: _safe_value(value) for key, value in sorted(attributes.items())}
    sequence = len(existing) + 1
    previous = existing[-1].event_sha256 if existing else "0" * 64
    event_id = hashlib.sha256(_canonical({"trace_id": scope.trace_id, "sequence": sequence, "event_type": event_type})).hexdigest()[:24]
    unsigned = {"sequence": sequence, "event_id": event_id, "event_type": event_type, "scope": asdict(scope), "timestamp": timestamp, "attributes": safe, "input_fingerprint": input_fingerprint, "output_fingerprint": output_fingerprint, "audit_event_id": audit_event_id, "previous_event_sha256": previous}
    return TraceEvent(sequence, event_id, event_type, scope, timestamp, safe, input_fingerprint, output_fingerprint, audit_event_id, previous, hashlib.sha256(_canonical(unsigned)).hexdigest())


def validate_trace(events: tuple[TraceEvent, ...]) -> None:
    if not events:
        raise TraceError("trace is empty")
    scope = events[0].scope; previous = "0" * 64
    for index, event in enumerate(events, start=1):
        if event.sequence != index or event.scope != scope or event.previous_event_sha256 != previous:
            raise TraceError("trace sequence, scope, or hash chain invalid")
        unsigned = {"sequence": event.sequence, "event_id": event.event_id, "event_type": event.event_type, "scope": asdict(event.scope), "timestamp": event.timestamp, "attributes": event.attributes, "input_fingerprint": event.input_fingerprint, "output_fingerprint": event.output_fingerprint, "audit_event_id": event.audit_event_id, "previous_event_sha256": event.previous_event_sha256}
        if event.event_sha256 != hashlib.sha256(_canonical(unsigned)).hexdigest():
            raise TraceError("trace event tampered")
        previous = event.event_sha256


def summarize_trace(events: tuple[TraceEvent, ...]) -> dict[str, object]:
    validate_trace(events)
    tokens = sum(int(event.attributes.get("tokens", 0)) for event in events)
    cost = sum(int(event.attributes.get("cost_microusd", 0)) for event in events)
    latency = sum(int(event.attributes.get("latency_ms", 0)) for event in events)
    return {"trace_id": events[0].scope.trace_id, "tenant_id": events[0].scope.tenant_id, "incident_id": events[0].scope.incident_id, "event_count": len(events), "total_tokens": tokens, "total_cost_microusd": cost, "total_latency_ms": latency, "errors": sum(event.event_type == "error" for event in events), "retries": sum(event.event_type == "retry" for event in events), "audit_event_ids": tuple(event.audit_event_id for event in events if event.audit_event_id), "trace_head_sha256": events[-1].event_sha256}
