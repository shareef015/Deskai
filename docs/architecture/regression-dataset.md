# Deterministic regression corpus

The regression corpus contains exactly 500 synthetic cases: 125 each for Outlook, printers, scanners, and Windows/network support. Normal, failure, security, and edge classes are also balanced at 125 cases each. All 44 supported incident classes and ten synthetic endpoints are represented.

Every record preserves symptoms, clarification, device state, diagnostic evidence, knowledge lineage, expected root cause, safe remediation, risk, approval, rollback, post-state, verification, employee response, and final status. It also binds the corresponding conversation, telemetry pack, authorization decision, and remediation execution outcome.

Stable UUIDs, per-case seeds, source digests, a canonical dataset digest, and a separate replay manifest enable byte-exact regeneration. Replicas derived from the same source incident stay in one split to prevent source-case leakage between the regression core and release gate.
