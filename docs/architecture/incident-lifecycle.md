# Persistent incident lifecycle

Incident status changes occur only through the lifecycle service. The state
machine has explicit edges, terminal states and evidence-backed guards. Client
bodies may request a target but cannot submit guard truth; consent, approvals,
pre-state, execution and verification are resolved from authoritative records.

The database update atomically matches tenant, incident, current state and
version. A successful transition increments the version and appends both an
incident-history event and a tamper-evident audit event in the same transaction.
Stale writers or illegal edges return conflict without partial history.

Resolution requires technical verification, employee confirmation and complete
audit records. The LLM may recommend a transition but cannot satisfy or bypass a
guard. Escalation always records a bounded human-readable reason.
