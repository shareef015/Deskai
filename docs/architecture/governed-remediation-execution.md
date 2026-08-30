# Governed Remediation Execution

The coordinator converts an exact validated approval into a signed capability token scoped to one tenant, incident, device, plan fingerprint, approval decision, action list, and capability list. Tokens expire within five minutes and cannot authorize another plan, device, or newly added action.

Execution requests contain a typed capability and bounded parameters, idempotency key, deadline, persistence flag, captured pre-state, and rollback capability. The gateway independently verifies the token signature, live plan fingerprint, action/capability pair, allowlist, expiry, and idempotency. Raw commands, shell, PowerShell, security bypass, credential collection, and device wipe are structurally unavailable.

The coordinator authorizes a dispatch envelope; only the endpoint capability gateway performs the implementation. Successful actions move to verification. Failed, partial, or timed-out mutations route to rollback when supported, otherwise to human recovery. No result is treated as resolution until separate technical, business-function, and employee verification succeeds.
