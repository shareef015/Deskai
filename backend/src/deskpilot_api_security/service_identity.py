from __future__ import annotations

from dataclasses import dataclass
import time


class ServiceIdentityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ServicePrincipal:
    workload_id: str
    audience: str
    tenant_id: str | None
    scopes: frozenset[str]
    issued_at: int
    expires_at: int
    certificate_thumbprint: str | None = None


class ServiceTrustPolicy:
    """Authorization layer for already-verified workload identities (mTLS/SPIFFE/OAuth client credentials)."""

    def __init__(self, *, expected_audience: str, allowed_workloads: dict[str, frozenset[str]], max_token_age_seconds: int = 300) -> None:
        self.expected_audience = expected_audience
        self.allowed_workloads = allowed_workloads
        self.max_token_age_seconds = max_token_age_seconds

    def authorize(self, principal: ServicePrincipal, *, required_scope: str, now: int | None = None) -> None:
        ts = int(time.time()) if now is None else now
        if principal.audience != self.expected_audience:
            raise ServiceIdentityError("service_audience_denied")
        if principal.expires_at <= ts or principal.issued_at > ts + 30:
            raise ServiceIdentityError("service_credential_expired")
        if ts - principal.issued_at > self.max_token_age_seconds:
            raise ServiceIdentityError("service_credential_too_old")
        allowed = self.allowed_workloads.get(principal.workload_id)
        if allowed is None:
            raise ServiceIdentityError("workload_not_trusted")
        if required_scope not in principal.scopes or required_scope not in allowed:
            raise ServiceIdentityError("service_scope_denied")
