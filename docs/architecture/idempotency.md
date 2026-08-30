# Idempotency and duplicate-request protection

Every mutating API request requires an `Idempotency-Key`. The durable scope is
tenant, normalized operation and a SHA-256 key hash; raw keys never enter logs.
A second SHA-256 fingerprint binds method, route, canonical body and relevant
preconditions such as `If-Match`.

The mutation and idempotency completion record commit together. The first caller
owns a random, expiring lease. The same key and fingerprint replays the original
encrypted status, safe headers and body; the same key with different input
returns conflict. In-progress duplicates receive a short retry response.

Replay data is AES-256-GCM encrypted and retained for 24 hours. Tenant RLS and
authenticated associated data prevent cross-tenant or cross-operation replay.
Idempotency does not replace optimistic concurrency or handler-level safety.
