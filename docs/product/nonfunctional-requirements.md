# Non-Functional Requirements, SLOs and Budgets

The initial private ten-device deployment targets 99.5% availability on one
server. A 99.9% target requires multi-node application capacity and off-host
state dependencies; it cannot honestly be promised by a single PC.

Security invariants have zero-error targets: cross-tenant access, endpoint
sessions without consent, and incident closure without technical plus employee
confirmation are never traded against availability or cost.

The pilot has an $800 monthly soft platform limit and $1,200 hard limit,
excluding customer-specific Microsoft/RMM licenses and staffing. AI work has
per-incident soft and hard ceilings. Reaching a budget ceiling triggers safe
degradation or human escalation, never a weaker authorization or guardrail.
