# Risk-Aware Remediation Planning

The planner runs only after evidence fusion has selected a grounded root cause. It has no tools and cannot approve, issue execution authority, mutate an endpoint, or declare resolution. Its input binds the tenant, incident, device, business function, evidence identifiers, and fusion provenance so a plan cannot be reused against a different scope.

Candidate actions are typed capabilities rather than commands. Each states prerequisites, expected effect, risk, blast radius, persistence, required pre-state, rollback, qualified approver, idempotency key, and technical, business-function, and employee verification. Security bypass, credential collection, destructive data removal, device wipe, unrestricted shell, and enterprise-policy bypass are rejected.

The deterministic planner prefers the lowest-risk eligible actions and limits the plan to four steps. Persistent changes require exact pre-state and rollback; shared-service or tenant-wide changes are always high risk. Every accepted plan moves to an independent approval interrupt. Execution remains the responsibility of the governed capability gateway after approval, and failed prerequisites or an unavailable safe action escalate.
