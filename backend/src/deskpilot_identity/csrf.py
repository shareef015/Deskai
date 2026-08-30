from __future__ import annotations

import base64
from hashlib import sha256
import hmac
import secrets
import time


class CsrfError(RuntimeError):
    pass


def issue_csrf_token(session_id: str, secret: bytes, *, now: int | None = None) -> str:
    ts = int(time.time()) if now is None else now
    nonce = secrets.token_urlsafe(24)
    payload = f"{session_id}.{ts}.{nonce}"
    mac = hmac.new(secret, payload.encode(), sha256).digest()
    sig = base64.urlsafe_b64encode(mac).decode().rstrip("=")
    return f"{ts}.{nonce}.{sig}"


def validate_csrf_token(token: str, session_id: str, secret: bytes, *, max_age_seconds: int = 3600, now: int | None = None) -> bool:
    ts_now = int(time.time()) if now is None else now
    parts = token.split(".")
    if len(parts) != 3:
        return False
    ts_text, nonce, supplied_sig = parts
    try:
        issued = int(ts_text)
    except ValueError:
        return False
    if issued > ts_now + 60 or issued + max_age_seconds < ts_now:
        return False
    payload = f"{session_id}.{issued}.{nonce}"
    mac = hmac.new(secret, payload.encode(), sha256).digest()
    expected = base64.urlsafe_b64encode(mac).decode().rstrip("=")
    return hmac.compare_digest(expected, supplied_sig)
