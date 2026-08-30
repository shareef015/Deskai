# PostgreSQL query performance

Indexes follow measured access paths rather than individual columns. Every
tenant-owned lookup begins with `tenant_id`; work queues and timelines use
keyset cursors with deterministic tie-breaker IDs. Partial indexes keep active
consent, approvals and open work small without indexing cold historical rows.

Production enables `pg_stat_statements` through the database operations layer.
Slow-query telemetry records fingerprints and plan statistics—not parameter
values. Index usage, bloat, autovacuum health, row-estimate accuracy and disk
spill are reviewed regularly. Index additions on populated production tables
use an approved online/concurrent runbook when transactional migration semantics
would otherwise cause blocking.
