# Specialist Subgraphs

The supervisor invokes isolated Outlook, printer, scanner, and Windows/network diagnostic subgraphs through one typed contract. Each receives only tenant and incident scope, device identity, a consent reference, a safe symptom summary, and bounded evidence identifiers. Supervisor conversation history and authorization state are not copied into specialist working memory.

Each specialist has a domain-specific read-only tool allowlist and independent step, tool-call, retrieval, and evidence budgets. Its nested graph performs collection, analysis, and finalization, then returns evidence references, hypotheses, clarification questions, a safe summary, completion status, and deterministic provenance. Raw tool output is never returned.

Specialists cannot remediate, approve, close incidents, or change lifecycle authority. Complete evidence returns to evidence fusion; insufficient or contradictory evidence returns to clarification; blocked or failed work escalates. Cross-tenant evidence, domain changes, unbounded output, and unsupported tools fail closed.
