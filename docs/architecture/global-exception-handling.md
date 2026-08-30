# Global exception handling

DeskPilot maps expected failures to a small, stable taxonomy and returns RFC-style
`application/problem+json` documents. Every response includes the request correlation
identifier, a machine-readable code, safe title, HTTP status and explicit retryability.
Retryable failures may include a bounded `Retry-After` value.

Unexpected exceptions always become the generic `internal_error` response. Stack
traces, exception messages, secrets, filesystem paths, queries, prompts and evidence
content are never returned to the caller. Validation errors do not echo rejected
values. All error responses use `Cache-Control: no-store`.

Detailed diagnostics are emitted internally through structured logging with the same
correlation identifier. Only the exception class and safe classification may be
recorded; raw exception values are prohibited. Security and privileged-operation
failures also create immutable audit events.

The same error codes will cross API, worker, LangGraph, RAG, MCP and endpoint-agent
boundaries so callers can make deterministic retry, escalation and user-message
decisions without inspecting implementation-specific exception strings.
