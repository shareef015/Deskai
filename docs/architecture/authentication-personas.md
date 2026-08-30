# Authentication, sessions and synthetic personas

DeskPilot accepts live identity only from the configured OIDC issuer and audience. Server-side sessions bind the authenticated subject, tenant, roles, mode and expiry; every authorization rechecks expiry, revocation, tenant, role and live/synthetic mode. Logout revokes the server record.

Recruiter personas exist only in non-production synthetic mode. A demo operator launches a short-lived persona session without passwords or live impersonation. Persona changes create a new session and hashed audit event instead of rewriting identity. Synthetic sessions cannot authorize live data or endpoint operations.
