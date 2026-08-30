# Redis cache, sessions and distributed state

Redis is never the durable system of record. It accelerates reconstructible
reads, stores encrypted browser sessions, coordinates bounded work and carries
ephemeral presence/progress. PostgreSQL and immutable evidence remain
authoritative.

Every key includes a keyed-HMAC tenant namespace; raw tenant, user and device
identifiers are prohibited. Session payloads use AES-256-GCM with a versioned
key, random nonce and the opaque session ID as authenticated associated data.
The cookie contains only that opaque ID. Loading a session refreshes idle TTL,
while absolute expiry remains inside the signed/encrypted session payload.

Locks use `SET NX PX`, random owner tokens and compare-token-delete Lua release.
TTL is bounded and irreversible operations additionally require durable fencing
or idempotency. Redis loss fails sessions and contested operations closed, but a
normal read-cache outage bypasses safely to the authoritative store.
