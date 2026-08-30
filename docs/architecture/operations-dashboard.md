# Operations Dashboard and Incident Queue

The operations queue exposes privacy-safe incident metadata for authenticated service-desk, operator and management roles. Tenant and environment mode are hard filters, so recruiter synthetic metrics cannot mix with live incidents.

SLA state, age and stalled-run flags are derived from durable timestamps. Priority ordering is deterministic by severity, SLA deadline and incident identifier; workload summaries expose approval backlog, rollback alerts and human ownership.

Queue-change events use a monotonic cursor for reconnect-safe live updates. The responsive table provides domain, severity, status, owner and actionable alert context without exposing conversation, prompts or raw endpoint evidence.
