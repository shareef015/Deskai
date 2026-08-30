# Agent Decision Trace, Provenance, and Observability

One trace scope binds a tenant, incident, graph thread, and correlation ID. Events cover graph transitions, agent decisions, retrieval, tool calls, human decisions, retries, errors, budgets, and terminal outcomes. Sequence numbers and a SHA-256 hash chain make missing, reordered, cross-scope, or modified events detectable.

The attribute allowlist captures evidence IDs, model ID, prompt version, configuration fingerprint, route reason, typed capability, status, error class, retries, tokens, micro-dollar cost, latency, and remaining budgets. Inputs and outputs are represented by fingerprints; raw prompts, model responses, endpoint output, document content, and credentials are not stored by default. Bounded string values receive secret and email redaction.

Operational summaries expose counts, cost, latency, errors, retries, linked audit IDs, and the trace-head fingerprint. Trace data references—but never replaces—the immutable audit ledger. Tenant-safe access, retention, sampling, and alerting remain policy-controlled, while the end-to-end lineage lets operators replay why an incident routed, paused, changed, rolled back, escalated, or closed.
