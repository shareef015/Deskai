# Multi-Agent Delegation Governance and Least Authority

A supervisor delegates only a typed, tenant-, incident-, and thread-scoped task. The contract fixes child agent, objective, input/output schema versions, evidence IDs, capabilities, tool calls, tokens, timeout, depth, and provenance. Delegated capabilities must be a strict subset of the parent’s live capability set and budget.

Depth is limited to two and concurrent fan-out to two specialists. Consent, remediation approval, capability-token issuance, execution, employee confirmation, closure, and knowledge publication authority never transfer to a child. Specialists can collect and return bounded evidence, clarification, or failure only.

Returned evidence must be a subset of the contract and the output schema and fingerprint must match. Tool, token, and time use cannot exceed delegation. Results arriving after cancellation, attempting authority, inventing evidence, or crossing scope fail closed. Accepted partial work remains explicitly insufficient rather than being promoted to a complete diagnosis.
