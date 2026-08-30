# Execution, Rollback and Verification

Execution begins only with an approved plan fingerprint, a signed pre-state and a single-use capability token scoped to the tenant, incident, device and exact typed actions. Action results are immutable.

Complete success proceeds to technical verification. Any partial, failed or timed-out action stops forward execution. Reversible failures enter verified rollback; missing rollback or failed rollback enters human recovery.

Resolution requires every plan-defined regression check plus the employee's explicit confirmation that the original business function works. Failed checks or a not-fixed response escalate instead of closing the incident.
