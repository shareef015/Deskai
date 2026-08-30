# Repositories and transaction boundaries

The API uses SQLAlchemy 2 asynchronous sessions with psycopg 3. A unit of work
owns exactly one session per request or durable worker job and exposes
tenant-bound repositories. Repositories may flush but never commit; the
application service decides when the complete business operation commits.

Every tenant repository receives a non-optional tenant identifier at
construction. Queries include that scope, inserts reject tenant mismatch, and a
cross-tenant identifier appears identical to a missing row. Database composite
foreign keys remain the second enforcement layer.

Incident writes use an explicit version for optimistic concurrency. Unique
constraints arbitrate duplicate creation, while exceptional pessimistic paths
must use bounded lock and statement timeouts. Network calls, model calls and
endpoint operations are prohibited inside database transactions.
