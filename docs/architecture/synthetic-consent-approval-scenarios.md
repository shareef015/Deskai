# Synthetic consent, approval, and rejection scenarios

The authorization corpus binds every generated incident to explicit diagnostic consent and a separate action-specific remediation decision. Consent is scoped to tenant, employee, device, incident, session, purpose, capabilities, issue time, and expiry. Approval also binds the exact action, risk, pre-state digest, rollback, requester, approver, and validity window.

Ten deterministic outcomes exercise authorization, decline, expiry, revocation, device, incident and tenant mismatch, unauthorized approver, proposer self-approval, and attempted AI authority. Every non-authorized outcome fails closed and prevents execution while producing immutable consent and approval audit references.

Employees control scoped diagnostic access. Medium and high-risk changes require an eligible independent human role. AI services, auditors, and the requester cannot manufacture or substitute approval.
