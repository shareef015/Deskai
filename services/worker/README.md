# Worker service

Durable, tenant-scoped background processing for outbox publication, SLA
evaluation, governed diagnostics, knowledge ingestion and evaluations. Jobs are
typed and versioned; handlers are idempotent and never execute arbitrary code.
