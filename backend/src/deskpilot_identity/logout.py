from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlencode

from .sessions import SessionManager


BACKCHANNEL_LOGOUT_EVENT = "http://schemas.openid.net/event/backchannel-logout"


class LogoutError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class VerifiedLogoutToken:
    issuer: str
    audience: tuple[str, ...]
    subject: str | None
    sid: str | None
    events: Mapping[str, object]
    issued_at: int
    jti: str
    nonce: str | None = None


def build_rp_logout_url(*, end_session_endpoint: str, id_token_hint: str | None, post_logout_redirect_uri: str | None, state: str | None) -> str:
    params: dict[str, str] = {}
    if id_token_hint:
        params["id_token_hint"] = id_token_hint
    if post_logout_redirect_uri:
        params["post_logout_redirect_uri"] = post_logout_redirect_uri
    if state:
        params["state"] = state
    return f"{end_session_endpoint}?{urlencode(params)}" if params else end_session_endpoint


class BackChannelLogoutHandler:
    def __init__(self, sessions: SessionManager, *, issuer: str, client_id: str) -> None:
        self.sessions = sessions
        self.issuer = issuer
        self.client_id = client_id
        self._seen_jti: set[str] = set()

    def apply(self, token: VerifiedLogoutToken, *, tenant_id: str | None = None, now: int) -> int:
        if token.issuer != self.issuer or self.client_id not in token.audience:
            raise LogoutError("logout_token_binding_mismatch")
        if BACKCHANNEL_LOGOUT_EVENT not in token.events or token.nonce is not None:
            raise LogoutError("invalid_logout_token_events")
        if not token.jti or token.jti in self._seen_jti:
            raise LogoutError("logout_token_replay")
        if token.sid is None and token.subject is None:
            raise LogoutError("logout_token_missing_sid_or_sub")
        self._seen_jti.add(token.jti)
        if token.sid:
            return self.sessions.revoke_oidc_sid(token.sid, reason="oidc_backchannel_logout", now=now)
        if tenant_id is None:
            raise LogoutError("tenant_required_for_subject_logout")
        return self.sessions.revoke_subject(token.subject or "", tenant_id, reason="oidc_backchannel_logout", now=now)
