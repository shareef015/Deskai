from __future__ import annotations

import re
from collections.abc import Mapping

_SECRET_KEYS = {"authorization", "access_token", "refresh_token", "id_token", "password", "secret", "cookie", "set-cookie"}
_BEARER = re.compile(r"(?i)bearer\s+[a-z0-9._~+\-/]+=*")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def redact_value(value: object, *, key: str = "") -> object:
    if key.lower() in _SECRET_KEYS or any(token in key.lower() for token in ("token", "password", "secret")):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(k): redact_value(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(v) for v in value]
    if isinstance(value, str):
        return _EMAIL.sub("[EMAIL_REDACTED]", _BEARER.sub("Bearer [REDACTED]", value))
    return value
