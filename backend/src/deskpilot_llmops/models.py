from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Mapping


def _stable_hex(value: str, size: int) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:size]


@dataclass(frozen=True, slots=True)
class TraceContext:
    trace_id: str
    span_id: str
    correlation_id: str
    tenant_id: str
    run_id: str
    sampled: bool = True

    @classmethod
    def root(cls, *, correlation_id: str, tenant_id: str, run_id: str) -> "TraceContext":
        seed = f"{correlation_id}|{tenant_id}|{run_id}"
        return cls(_stable_hex(seed, 32), _stable_hex(seed + "|root", 16), correlation_id, tenant_id, run_id)

    @classmethod
    def from_traceparent(cls, *, traceparent: str, correlation_id: str, tenant_id: str, run_id: str) -> "TraceContext":
        parts = traceparent.lower().split("-")
        if len(parts) != 4 or parts[0] != "00" or len(parts[1]) != 32 or len(parts[2]) != 16 or parts[3] not in {"00", "01"}:
            raise ValueError("invalid_traceparent")
        if not all(ch in "0123456789abcdef" for ch in parts[1] + parts[2]) or set(parts[1]) == {"0"} or set(parts[2]) == {"0"}:
            raise ValueError("invalid_traceparent")
        return cls(parts[1], parts[2], correlation_id, tenant_id, run_id, parts[3] == "01")

    def child(self, name: str, sequence: int) -> "TraceContext":
        return TraceContext(
            self.trace_id,
            _stable_hex(f"{self.trace_id}|{self.span_id}|{name}|{sequence}", 16),
            self.correlation_id,
            self.tenant_id,
            self.run_id,
            self.sampled,
        )

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampled else '00'}"


@dataclass(frozen=True, slots=True)
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    stage: str
    started_at: float
    ended_at: float
    status: str
    attributes: Mapping[str, object] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return max(0.0, (self.ended_at - self.started_at) * 1000.0)


@dataclass(frozen=True, slots=True)
class LogRecord:
    timestamp: float
    severity: str
    event_name: str
    message: str
    trace_id: str
    span_id: str
    correlation_id: str
    tenant_id: str
    run_id: str
    attributes: Mapping[str, object] = field(default_factory=dict)
