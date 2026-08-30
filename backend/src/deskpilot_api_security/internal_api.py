from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request

from .service_identity import ServiceIdentityError, ServicePrincipal, ServiceTrustPolicy


ServiceCredentialVerifier = Callable[[Request], Awaitable[ServicePrincipal]]


def require_service_identity(
    *,
    verifier: ServiceCredentialVerifier,
    policy: ServiceTrustPolicy,
    required_scope: str,
):
    """FastAPI dependency factory for internal APIs.

    The verifier must cryptographically authenticate the workload using a mature adapter
    (mTLS/SPIFFE/OAuth client credentials). This layer never trusts caller-supplied identity headers directly.
    """

    async def dependency(request: Request) -> ServicePrincipal:
        try:
            principal = await verifier(request)
            policy.authorize(principal, required_scope=required_scope)
            return principal
        except ServiceIdentityError as exc:
            raise HTTPException(status_code=403, detail="service_identity_denied") from exc
        except Exception as exc:
            # Do not reveal verifier/JWT/certificate failure details to the caller.
            raise HTTPException(status_code=401, detail="service_authentication_failed") from exc

    return dependency
