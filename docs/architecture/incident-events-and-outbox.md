# Incident events and transactional outbox

Every incident event uses a versioned envelope containing tenant, incident,
event type, aggregate version, actor, correlation, causation, UTC time and a
bounded allowlisted payload. Aggregate version supplies per-incident order;
consumers must not assume a global order.

The event service writes append-only incident history and an immutable outbox
identity in the same PostgreSQL transaction. Publication happens afterward.
Delivery is at least once, so consumers deduplicate by event ID and enforce
their own processed-event uniqueness.

Workers claim pending rows with bounded batches and `SKIP LOCKED`, update only
delivery metadata, retry with backoff, and dead-letter after twelve attempts.
The original topic, partition key, schema, payload and timestamps cannot change.
Publishing never occurs inside the business transaction.
