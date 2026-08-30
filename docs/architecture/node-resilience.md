# Node Resilience

Every external or fallible graph node executes inside an explicit resilience envelope. The envelope applies a bounded deadline, classifies failures, retries only transient categories with deterministic backoff, records safe attempt events, and preserves cancellation semantics.

Validation, authorization, policy, scope, permanent, and unknown failures are never retried. A dependency-scoped circuit opens after three consecutive failures, rejects calls during its cooldown, permits one half-open probe, and closes only after success. Circuit state is designed for durable tenant/node/dependency persistence rather than process-local memory.

If an operation reports a partial mutation, recovery requires one idempotent compensation attempt and a validated idempotency key. Missing or failed compensation escalates for human intervention and never hides the original failure. All outcomes include deterministic provenance without raw exceptions or secrets.
