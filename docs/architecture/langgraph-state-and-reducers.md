# Typed graph state and reducers

DeskPilot uses separate typed input, internal, and output schemas. Immutable tenant, incident, thread, correlation, employee, and device identifiers establish scope. Internal state carries the lifecycle phase, bounded budgets, consent, approval, hypotheses, evidence, safe errors, retry counts, remediation references, audit references, and terminal status.

Nodes return partial updates; they do not mutate state. Message, evidence, error, and retry channels use explicit `Annotated` reducers so parallel writes cannot silently overwrite one another. Collection reducers deduplicate stable identifiers, resolve duplicate writes canonically, sort deterministically, and retain bounded history. Retry counters use monotonic maximums capped by policy.

Runtime validation rejects cross-tenant or cross-incident evidence, unbounded content, duplicate identifiers, invalid budgets, execution without approval, and inconsistent terminal state. These dependency-light schemas can be imported and tested before graph construction while remaining directly compatible with LangGraph `StateGraph`.
