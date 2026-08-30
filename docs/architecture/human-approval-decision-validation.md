# Human Approval Request and Decision Validation

An approval packet is created only for an unchanged remediation plan that passed the independent critic. It binds tenant, incident, device, graph thread, checkpoint, plan ID and fingerprint, critic fingerprint, risk, action and capability IDs, requester, plan author, qualified roles, issue time, and expiry. The packet is immutable and deterministic for the same checkpointed plan.

The validator accepts only an authenticated human in the same tenant with a role qualified for the plan’s risk. The approver must be independent of the plan author and approval requester. AI services and auditors cannot approve. Rejected, expired, revoked, mismatched, or plan-mutated packets fail closed; every decision needs an explicit reason.

Decision fingerprints make exact retries idempotent and reject conflicting replay. An approved decision advances only the exact plan fingerprint to governed execution; rejection cancels the proposed change. The component records human authority but never supplies, predicts, or substitutes for it, and it cannot execute an action.
