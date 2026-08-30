# Durable human interrupts

Diagnostic consent, remediation approval, and employee confirmation are separate graph nodes with one stable `interrupt()` call each. The JSON payload binds request version, tenant, incident, thread, checkpoint, employee, device, purpose, capabilities, risk, requester, action, issue time, expiry, and revocation state. A durable checkpointer preserves the paused execution.

The graph never accepts a raw browser decision. An authenticated server-side gate revalidates scope, expiry, revocation, assigned-device ownership, decision vocabulary, risk-matched role, and segregation of duties. AI identities and auditors are denied. Only the validated envelope is passed through `Command(resume=...)`, and the resumed node checks its request identity again.

Identical repeated decisions are idempotent; a conflicting second decision is rejected. Declined consent cancels endpoint diagnostics, rejected approval escalates without execution, and failed employee verification prevents resolution. Replaying before an interrupt deliberately requires a new human decision.
