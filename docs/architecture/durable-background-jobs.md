# Durable background jobs

Jobs are PostgreSQL records created in the same transaction as the state that
requires work. Each envelope has an allowlisted type, schema version, tenant,
bounded payload and idempotency key. Workers never accept arbitrary code names.

A worker claims tenant-scoped work with `FOR UPDATE SKIP LOCKED`, a random lease
token and bounded expiry. Completion requires the same unexpired token. Handlers
perform external work outside the claim transaction and must be idempotent
because delivery is at least once.

Retryable failures use exponential backoff with full jitter for at most eight
attempts. Invalid payloads, unsupported types, authorization denial and tenant
mismatch dead-letter immediately. Attempt history is immutable; authorized
manual requeue creates an audited new job rather than rewriting history.
