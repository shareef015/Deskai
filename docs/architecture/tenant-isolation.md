# Multi-tenant isolation

The authenticated identity supplies the tenant claim. Request bodies, query
parameters, model output and tool output can never choose or override it. The
claim becomes immutable request/job context, constructs a tenant-bound
repository and is bound with `set_config` as transaction-local PostgreSQL state.

All tenant-owned tables have forced row-level security with matching `USING`
and `WITH CHECK` predicates. Missing context matches no tenant row. Composite
tenant foreign keys independently block cross-tenant relationships. The runtime
database role is neither a superuser nor table owner and cannot bypass RLS;
schema migration uses a separate controlled identity.

Transaction-local settings prevent context reuse across pooled connections.
Security tests must exercise select, insert, update and delete attacks in both
directions, missing context, forged request fields and connection-pool reuse.
Operational support across tenants occurs as individually audited tenant-scoped
sessions; there is no universal application query path.
