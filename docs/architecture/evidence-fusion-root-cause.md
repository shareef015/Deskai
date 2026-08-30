# Evidence Fusion and Root-Cause Reasoning

The fusion agent has no diagnostic or remediation tools. It receives already-scoped specialist findings, typed endpoint telemetry, filtered RAG guidance, employee observations, and inventory facts. Every record must belong to the active tenant and incident and retain a unique evidence identifier, source type, source identity, observation key, reliability, and freshness.

Candidate causes explicitly list supporting and contradicting evidence. Deterministic source weights rank candidates, but a root cause is eligible only when at least two independent source types support it and the governed score threshold is met. RAG is guidance rather than observed machine state and can never establish a cause by itself.

Conflicting reliable values for the same observation remain visible. Close high-scoring candidates are not silently tie-broken. Weak evidence returns to clarification; material contradiction escalates; only a grounded winner advances to remediation planning. The result includes ranked hypotheses, evidence links, contradiction keys, a reason, and a deterministic provenance digest. The agent cannot approve, execute, or claim resolution.
