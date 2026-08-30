# Structured logging and correlation

Every runtime boundary emits newline-delimited JSON with a stable event name,
UTC timestamp, severity, service, environment and correlation identifier. The
same correlation identifier crosses API, worker, LangGraph, RAG, MCP gateway,
endpoint-agent and audit boundaries. Trace, incident and audit-event identifiers
provide links without turning operational logs into the authoritative audit record.

## Privacy and safety

Structured fields pass through recursive key- and pattern-based redaction. Secret
keys, authorization values, cookies, connection strings and private keys are never
logged. Email addresses are masked, strings are bounded, tenant IDs are converted
to deployment-salted stable hashes, and raw conversations, retrieved documents and
hidden model reasoning are prohibited.

The formatter blocks accidental unstructured messages instead of serializing them.
Production exception events use error codes and safe classifications; detailed
diagnostic evidence remains in access-controlled evidence stores.

## Retention and access

Operational logs default to 30 days and security logs to 180 days, with explicit
maximums. Log access is role-scoped and audited. Immutable audit records have their
own retention policy and evidence lineage; duplicating them into logs does not make
the log copy authoritative.
