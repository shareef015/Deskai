# Context Compression and Token-Budget Governance

Compression starts only when the current context plus the next node’s reserved budget would exceed 12,000 tokens. It targets 6,000 tokens using deterministic bounded summaries of recent redacted history rather than asking a model to reinterpret safety state.

Tenant, incident, thread, checkpoint, employee, device, phase, consent, approval, evidence IDs, contradictions, selected cause, plan and rollback state, execution, verification, human decisions, budgets, audit IDs, trace head, and state version are pinned verbatim. A summary cannot override or replace these fields.

Every source item keeps sequence, type, source fingerprint, token estimate, and freshness epoch. The compressed artifact binds the complete covered-item list, source-chain head, scope, pinned state, token counts, and compressor version. Rehydration fails if history, freshness, scope, or any pinned value changed, preventing stale approval, lost contradiction, or cross-tenant context reuse.
