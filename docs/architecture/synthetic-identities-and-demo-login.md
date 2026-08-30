# Synthetic identities and demo login

Every fictional workforce member has deterministic Entra-shaped identity attributes, including stable object and tenant identifiers, subject, role hints and a reserved `demo.invalid` username. These records are fixtures, not real directory accounts or signed identity-provider tokens.

The persona picker is available only in development or test with explicit synthetic mode and a trusted private demo origin. It creates an opaque, rotated, server-side session with CSRF protection, idle and absolute expiry. It uses no passwords and cannot run in production. Role claims assist display and routing only; database assignments remain authoritative for every permission decision.
