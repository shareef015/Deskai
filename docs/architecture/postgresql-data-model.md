# PostgreSQL production data model

PostgreSQL is the system of record for tenant configuration, endpoint identity,
incident state, append-only history, evidence lineage, human authorization,
remediation, verification, durable AI execution and audit events.

Every tenant-owned row carries `tenant_id`. Relationships use composite
`(tenant_id, id)` foreign keys so a reference cannot silently cross tenant
boundaries. Later control-plane work will add enforced row-level security in
addition to these structural constraints.

Large evidence payloads, raw telemetry and graph state do not live directly in
relational rows. The database stores governed object references, SHA-256
digests, classification and retention metadata. Passwords, tokens, certificate
private keys and other credential material are prohibited.

Incident and audit history are append-only. Human consent and approval are
independent records; an AI run or checkpoint never represents authorization.
Remediation execution requires an idempotency key and a pre-change state
reference, while verification stores technical outcome separately from the
employee's confirmation.
