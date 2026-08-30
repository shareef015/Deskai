# DeskPilot Identity Backend — 

Framework-neutral production identity core for OIDC, opaque server sessions, RBAC/ABAC, tenant isolation, step-up grants, logout propagation, identity audit, permission-drift invalidation, and deterministic security tests.

The core deliberately does **not** implement JWT cryptographic verification itself. Wire `OidcFlow` to a mature OIDC/JWT library or the enterprise IdP SDK and verify issuer, audience, signature, expiry, nonce and key rotation before constructing `VerifiedIdToken`. Access/refresh tokens remain server-side.

## Local dependency-free core tests

```bash
cd backend
python -m unittest discover -s tests -v
```

## Production adapters

Use the identity core from the FastAPI/API layer with:
- OIDC Authorization Code + PKCE (`S256`)
- server-side session storage (PostgreSQL/Redis)
- HttpOnly `__Host-` session cookie
- durable append-only audit sink
- IdP front/back-channel logout integration
- centralized policy middleware on every protected API request
