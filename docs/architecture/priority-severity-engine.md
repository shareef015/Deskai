# Priority, severity and business impact

Final incident priority is calculated by deterministic policy, never accepted
from a client or LLM. Verified impact and urgency scores feed a versioned matrix;
confirmed security/safety risk or a complete site outage escalates to P1. VIP
status alone has no effect.

Each decision stores priority, severity, bounded input scores, policy version,
reason codes and calculation time. New evidence can trigger version-checked
reclassification. SLA targets consume this result in the assignment/timer layer.

Human overrides require explicit authorization, a reason and expiry. The
original and replacement values remain in immutable tenant-scoped history and
the decision is audited. AI may recommend review but cannot perform an override.
