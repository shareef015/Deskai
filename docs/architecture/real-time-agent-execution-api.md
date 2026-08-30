# Real-Time Agent Execution API, SSE Timeline, and Operator Controls

Authenticated start, resume, cancel, and event-stream operations bind tenant, incident, graph thread, command ID, and checkpoint. Start is idempotent and cannot create a second active execution. Resume requires the exact current checkpoint plus a server-validated human-decision fingerprint. Terminal executions are immutable.

Timeline events use monotonic cursors, stable event IDs, and event fingerprints. A reconnect supplies its last cursor and receives only later events. Public fields are limited to phase, status, agent, route reason, interrupt type, decision requirement, evidence count, safe error class, recovery route, and trace head. Prompts, model content, endpoint output, credentials, and document content are never streamed.

Operator controls remain role- and tenant-scoped. Synthetic recruiter demonstrations additionally require the demo-operator role and cannot control live endpoints. Command idempotency, optimistic checkpoint concurrency, durable cursor semantics, terminal protection, and privacy-safe SSE encoding prevent duplicate or hidden execution while keeping the journey visible.
