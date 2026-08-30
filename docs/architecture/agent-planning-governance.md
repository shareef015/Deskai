# Agent Planning Governance and Plan Validation

Planning begins with a tenant- and incident-scoped objective drawn from an approved registry. Plans are limited to eight steps, twelve tool calls, 4,000 planning tokens, ten minutes, and two replans. Every replan creates a new immutable version linked to the previous plan fingerprint.

Steps declare an objective, dependencies, evidence IDs, optional allowlisted tool, risk, and expected typed output. Dependencies must form a DAG. Risky steps require available evidence. Consent or approval bypass, security disablement, credential collection, evidence hiding, unverified closure, tenant expansion, and arbitrary command execution are forbidden at both plan and step level.

The validator fingerprints the exact scope, budgets, lineage, ordered graph, and steps. An independent critic must pass that same fingerprint before orchestration. Any mutation requires a new version and review. Missing evidence, hidden dependencies, understated tool count, exhausted budget, forbidden goal, excessive replanning, or critic mismatch fails closed.
