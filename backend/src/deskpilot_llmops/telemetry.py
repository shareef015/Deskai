from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping

from .metrics import MetricRegistry
from .models import LogRecord, SpanRecord, TraceContext
from .redaction import redact_value


@dataclass(slots=True)
class _OpenSpan:
    context: TraceContext
    parent_span_id: str | None
    name: str
    stage: str
    started_at: float
    attributes: dict[str, object]


class TelemetryRecorder:
    def __init__(self, *, metrics: MetricRegistry | None = None) -> None:
        self.metrics = metrics or MetricRegistry()
        self._spans: list[SpanRecord] = []
        self._logs: list[LogRecord] = []
        self._sequence = 0

    def root_context(self, *, correlation_id: str, tenant_id: str, run_id: str) -> TraceContext:
        return TraceContext.root(correlation_id=correlation_id, tenant_id=tenant_id, run_id=run_id)

    @contextmanager
    def span(self, parent: TraceContext, *, name: str, stage: str, now: float, attributes: Mapping[str, object] | None = None) -> Iterator[TraceContext]:
        self._sequence += 1
        child = parent.child(name, self._sequence)
        opened = _OpenSpan(child, parent.span_id, name, stage, now, dict(redact_value(dict(attributes or {}))))
        error: BaseException | None = None
        try:
            yield child
        except BaseException as exc:
            error = exc
            raise
        finally:
            end = max(now, now if error is None else now)
            status = "ERROR" if error is not None else "OK"
            attrs = dict(opened.attributes)
            if error is not None:
                attrs["error.type"] = type(error).__name__
            self._spans.append(SpanRecord(child.trace_id, child.span_id, opened.parent_span_id, name, stage, opened.started_at, end, status, attrs))
            self.metrics.record("deskpilot.operation.count", 1, unit="{operation}", labels={"stage": stage, "status": status.lower()})

    def record_span(self, parent: TraceContext, *, name: str, stage: str, started_at: float, ended_at: float, status: str = "OK", attributes: Mapping[str, object] | None = None) -> TraceContext:
        self._sequence += 1
        child = parent.child(name, self._sequence)
        safe = dict(redact_value(dict(attributes or {})))
        self._spans.append(SpanRecord(child.trace_id, child.span_id, parent.span_id, name, stage, started_at, ended_at, status, safe))
        self.metrics.record("deskpilot.operation.count", 1, unit="{operation}", labels={"stage": stage, "status": status.lower()})
        self.metrics.record("deskpilot.operation.duration", max(0.0, ended_at - started_at), unit="s", labels={"stage": stage, "status": status.lower()})
        return child

    def log(self, context: TraceContext, *, timestamp: float, severity: str, event_name: str, message: str, attributes: Mapping[str, object] | None = None) -> None:
        self._logs.append(LogRecord(timestamp, severity, event_name, str(redact_value(message)), context.trace_id, context.span_id, context.correlation_id, context.tenant_id, context.run_id, dict(redact_value(dict(attributes or {})))))

    @property
    def spans(self) -> tuple[SpanRecord, ...]:
        return tuple(self._spans)

    @property
    def logs(self) -> tuple[LogRecord, ...]:
        return tuple(self._logs)
