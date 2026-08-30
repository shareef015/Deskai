# Incident API

The incident API exposes create, read, keyset-list and metadata-update operations.
Deletion is intentionally unavailable, and lifecycle status transitions are
reserved for the dedicated state machine rather than generic PATCH.

Tenant identity comes only from the verified principal. Every operation invokes
the authoritative authorization gateway and opens a tenant-bound unit of work.
Request schemas reject unknown fields and never accept tenant identifiers.

Updates require an `If-Match` version and use an atomic tenant, incident and
version predicate. Lists use `(opened_at, id)` keyset cursors and bounded limits.
Responses omit tenant IDs and use private no-store caching.
