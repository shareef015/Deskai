from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import secrets
import time
from typing import Awaitable, Callable, Mapping
from urllib.parse import urlencode

from .models import Principal, Role


class OidcError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OidcConfig:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    client_id: str
    redirect_uri: str
    scopes: tuple[str, ...] = ("openid", "profile", "email")
    acr_values: tuple[str, ...] = ()
    transaction_ttl_seconds: int = 600


@dataclass(frozen=True, slots=True)
class AuthorizationTransaction:
    state: str
    nonce: str
    code_verifier: str
    code_challenge: str
    created_at: int
    return_path: str
    step_up_action: str | None = None
    step_up_resource_id: str | None = None
    step_up_session_id: str | None = None


@dataclass(frozen=True, slots=True)
class VerifiedIdToken:
    issuer: str
    audience: tuple[str, ...]
    subject: str
    nonce: str
    expires_at: int
    issued_at: int
    auth_time: int
    tenant_id: str
    roles: frozenset[Role]
    capabilities: frozenset[str]
    acr: str | None = None
    amr: tuple[str, ...] = ()
    email: str | None = None
    oidc_sid: str | None = None
    permission_version: int = 1


TokenExchange = Callable[[str, str], Awaitable[Mapping[str, object]]]
IdTokenVerifier = Callable[[str], Awaitable[VerifiedIdToken]]


class TransactionStore:
    def __init__(self) -> None:
        self._items: dict[str, AuthorizationTransaction] = {}

    def put(self, tx: AuthorizationTransaction) -> None:
        self._items[tx.state] = tx

    def consume(self, state: str) -> AuthorizationTransaction | None:
        return self._items.pop(state, None)


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


class OidcFlow:
    def __init__(self, config: OidcConfig, *, transactions: TransactionStore | None = None) -> None:
        self.config = config
        self.transactions = transactions or TransactionStore()

    def begin(
        self,
        *,
        return_path: str = "/",
        step_up_action: str | None = None,
        step_up_resource_id: str | None = None,
        step_up_session_id: str | None = None,
        force_reauth: bool = False,
        now: int | None = None,
    ) -> tuple[str, AuthorizationTransaction]:
        ts = int(time.time()) if now is None else now
        verifier, challenge = _pkce_pair()
        tx = AuthorizationTransaction(
            state=secrets.token_urlsafe(32),
            nonce=secrets.token_urlsafe(32),
            code_verifier=verifier,
            code_challenge=challenge,
            created_at=ts,
            return_path=return_path if return_path.startswith("/") and not return_path.startswith("//") else "/",
            step_up_action=step_up_action,
            step_up_resource_id=step_up_resource_id,
            step_up_session_id=step_up_session_id,
        )
        self.transactions.put(tx)
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "state": tx.state,
            "nonce": tx.nonce,
            "code_challenge": tx.code_challenge,
            "code_challenge_method": "S256",
        }
        if self.config.acr_values:
            params["acr_values"] = " ".join(self.config.acr_values)
        if force_reauth:
            params["prompt"] = "login"
            params["max_age"] = "0"
        return f"{self.config.authorization_endpoint}?{urlencode(params)}", tx

    async def complete(
        self,
        *,
        code: str,
        state: str,
        exchange: TokenExchange,
        verify_id_token: IdTokenVerifier,
        now: int | None = None,
    ) -> tuple[Principal, AuthorizationTransaction, Mapping[str, object]]:
        ts = int(time.time()) if now is None else now
        tx = self.transactions.consume(state)
        if tx is None:
            raise OidcError("invalid_or_replayed_state")
        if tx.created_at + self.config.transaction_ttl_seconds < ts:
            raise OidcError("authorization_transaction_expired")
        tokens = await exchange(code, tx.code_verifier)
        raw = tokens.get("id_token")
        if not isinstance(raw, str) or not raw:
            raise OidcError("missing_id_token")
        claims = await verify_id_token(raw)
        self._validate_claims(claims, tx=tx, now=ts)
        principal = Principal(
            user_id=claims.subject,
            tenant_id=claims.tenant_id,
            subject=claims.subject,
            roles=claims.roles,
            capabilities=claims.capabilities,
            attributes={"email": claims.email or ""},
            auth_time=claims.auth_time,
            acr=claims.acr,
            amr=claims.amr,
            oidc_sid=claims.oidc_sid,
            permission_version=claims.permission_version,
        )
        return principal, tx, tokens

    def _validate_claims(self, claims: VerifiedIdToken, *, tx: AuthorizationTransaction, now: int) -> None:
        if claims.issuer != self.config.issuer:
            raise OidcError("issuer_mismatch")
        if self.config.client_id not in claims.audience:
            raise OidcError("audience_mismatch")
        if not secrets.compare_digest(claims.nonce, tx.nonce):
            raise OidcError("nonce_mismatch")
        if claims.expires_at <= now or claims.issued_at > now + 60 or claims.auth_time > now + 60:
            raise OidcError("invalid_token_time")
        if not claims.subject or not claims.tenant_id:
            raise OidcError("missing_identity_binding")
