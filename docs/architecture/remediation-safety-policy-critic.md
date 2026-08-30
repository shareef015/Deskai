# Remediation Safety and Policy Critic

The critic is an independent gate between remediation planning and human approval. It receives the immutable plan and fusion provenance plus tenant, incident, device, root cause, plan author, approval requester, and proposed approver identities. It has no tools and cannot rewrite, approve, execute, or close a plan.

Every typed action is checked for evidence linkage, governed capability membership, prohibited behavior, risk and blast-radius consistency, prerequisites, unique idempotency, persistent-change pre-state and rollback, qualified approval, segregation of duties, and technical, business-function, and employee verification. Findings are deterministic and retain the affected action identifier.

A clean review advances the unchanged plan to approval. Blocking gaps return it to planning as a new immutable plan version. Critical security, blast-radius, or approver-independence violations escalate to a human owner. Findings and the reviewed plan fingerprint remain auditable; the critic never silently repairs or suppresses a defect.
