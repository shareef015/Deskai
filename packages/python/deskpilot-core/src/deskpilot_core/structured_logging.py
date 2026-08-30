from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Mapping


_SENSITIVE_KEYS = re.compile(
    r"password|passwd|secret|token|authorization|cookie|api[_-]?key|private[_-]?key|connection[_-]?string",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]+")
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_MAX_TEXT = 2048


class LoggingContractError(ValueError):
    """Raised when mandatory structured-log context is absent or invalid."""


@dataclass(frozen=True, slots=True)
class LogContext:
    correlation_id: str
    service: str
    environment: str
    tenant_id: str | None = None
    incident_id: str | None = None
    trace_id: str | None = None
    audit_event_id: str | None = None

    def validate(self) -> None:
        if not self.correlation_id.strip():
            raise LoggingContractError("correlation_id is required")
        if not self.service.strip() or not self.environment.strip():
            raise LoggingContractError("service and environment are required")


def _safe_text(value: str) -> str:
    text = _BEARER.sub("Bearer [REDACTED]", value)
    text = _EMAIL.sub("[EMAIL_REDACTED]", text)
    return text[:_MAX_TEXT]


def redact(value: Any, *, key: str = "") -> Any:
    if _SENSITIVE_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [redact(item, key=key) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _safe_text(str(value))


def tenant_log_key(tenant_id: str, salt: str) -> str:
    if not tenant_id or not salt:
        raise LoggingContractError("tenant log key requires identifier and deployment salt")
    return hashlib.sha256(f"{salt}:{tenant_id}".encode()).hexdigest()[:24]


def build_log_event(
    level: str,
    event: str,
    context: LogContext,
    fields: Mapping[str, Any] | None = None,
    *,
    now: datetime | None = None,
    tenant_salt: str | None = None,
) -> dict[str, Any]:
    context.validate()
    if not event or not re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}", event):
        raise LoggingContractError("event name must be stable machine-readable text")
    instant = now or datetime.now(UTC)
    if instant.tzinfo is None:
        raise LoggingContractError("log timestamp must be timezone-aware")
    context_values = asdict(context)
    tenant_id = context_values.pop("tenant_id")
    if tenant_id:
        if not tenant_salt:
            raise LoggingContractError("tenant salt is required when tenant context is present")
        context_values["tenant_key"] = tenant_log_key(tenant_id, tenant_salt)
    payload: dict[str, Any] = {
        "timestamp": instant.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "level": level.upper(),
        "event": event,
        **{key: value for key, value in context_values.items() if value is not None},
        "fields": redact(fields or {}),
    }
    return payload


class JsonLogFormatter(logging.Formatter):
    """Formats pre-built DeskPilot event dictionaries as one-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "deskpilot_event", None)
        if not isinstance(event, Mapping):
            event = {
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "level": record.levelname,
                "event": "runtime.unstructured_log_blocked",
                "service": "unknown",
                "environment": "unknown",
                "correlation_id": "missing",
                "fields": {"message": "unstructured log call omitted"},
            }
        return json.dumps(redact(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def emit(logger: logging.Logger, payload: Mapping[str, Any]) -> None:
    level = logging._nameToLevel.get(str(payload.get("level", "INFO")).upper(), logging.INFO)
    logger.log(level, "structured-event", extra={"deskpilot_event": dict(payload)})

