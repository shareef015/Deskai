# Human Interrupt Inbox and Approval Console

The inbox is the durable human-authority boundary between graph interrupts and authenticated decisions. It exposes separate queues for employee diagnostic consent, qualified remediation approval, and employee outcome confirmation. Tenant, subject, role, incident, thread and checkpoint scope are revalidated when the decision is submitted rather than trusted from the browser.

Review packets contain concise summaries, risk, referenced evidence IDs, typed action IDs, a before/after plan diff, expiry and rollback availability. Raw endpoint output, prompts, secrets and unrestricted evidence content are prohibited. Remediation requesters cannot approve their own plans.

Every decision is immutable and idempotent. Expired, revoked or otherwise terminal interrupts cannot resume execution. Privacy-safe events use a monotonic cursor so the console can reconnect without duplicating decisions or exposing actor identifiers.
