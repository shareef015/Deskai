# Database migration operations

Alembic is the only schema writer. Each deployment resolves its database URL at
runtime, acquires a transaction-scoped PostgreSQL advisory lock, applies one
reviewed revision at a time and verifies the resulting revision and schema.
Application startup never invokes `create_all`.

The baseline migration verifies the SHA-256 digest of the authoritative schema
before execution, preventing a historical migration from silently changing.
Any schema modification requires a new immutable revision. The PostgreSQL
extension is infrastructure-owned and is intentionally not removed on rollback.

CI must exercise `upgrade head -> downgrade base -> upgrade head` on an
ephemeral PostgreSQL instance. Production uses forward repair by default;
downgrade requires an approved recovery decision and verified backup. Breaking
changes follow expand/backfill/switch/contract across compatible releases.
