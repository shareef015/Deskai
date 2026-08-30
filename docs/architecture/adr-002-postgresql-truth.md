# ADR: PostgreSQL as Durable Truth

Status: accepted.

PostgreSQL stores tenant records, incidents, LangGraph checkpoints, approvals
and audit events. Redis is limited to ephemeral acceleration. This prevents a
cache outage or eviction from becoming an authorization or incident-history
failure.
