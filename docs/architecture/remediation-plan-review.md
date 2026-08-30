# Remediation Plan Review

Every remediation proposal is an immutable fingerprinted action graph. Reviewers see typed capabilities, risk, dependencies, evidence references, before/after state, rollback and verification requirements before deciding.

Approval is authenticated, tenant-scoped, checkpoint-bound and restricted to qualified independent approvers. Requesters cannot approve their own plan. Expired, superseded, rejected or already decided plans cannot execute, and rejected plans require a reason.

Execution must report every action. Success proceeds to verification; partial or failed execution routes to rollback when all failed actions are reversible, otherwise to human recovery.
