# System Architecture

DeskPilot uses six stateless runtime boundaries—web, API, AI, RAG, MCP gateway
and worker—plus PostgreSQL, Redis, telemetry and a signed Windows endpoint
agent. The ten-device pilot can run the server-side containers on one private
host, while preserving boundaries that allow later horizontal scaling.

The API is the control plane. LangGraph may recommend a typed tool request but
cannot reach an endpoint directly. The API authenticates the actor, resolves
tenant and device context, evaluates consent and approval, and issues a narrow
capability. The MCP gateway validates that capability and communicates with the
correct endpoint over mutual TLS. The endpoint independently validates scope
before executing an allowlisted operation.

PostgreSQL is durable truth for incidents, checkpoints, approvals and audit.
Redis accelerates sessions, locks, limits and caches but is never authoritative.
External model or observability providers are disabled by default in the
private deployment profile.
