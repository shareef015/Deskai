# Synthetic remediation, failure, and rollback

Every generated incident receives a deterministic remediation plan containing a typed allowlisted action, bounded arguments, action-specific authorization reference, pre-state digest, risk, rollback, retry ceiling, timeout, and idempotency key.

Seven outcomes exercise successful execution, failed precondition, failure without change, partial change with verified rollback, rollback failure, timeout with compensation, and duplicate idempotent replay. A changed partial state must be compensated or rolled back. Verification compares the restored digest to the captured pre-state; rollback failure retains evidence and escalates safely.

The corpus is an offline execution model. It cannot run shell commands, PowerShell, endpoint tools, or real remediations. It provides deterministic evidence for later controlled-execution and compensation tests.
