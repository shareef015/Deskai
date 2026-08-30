# Quality-Aware Model Routing and Governed Fallback

The router treats model selection as deterministic policy. Each request declares tenant, task, risk, complexity, required capabilities, data class, estimated tokens, latency SLO, remaining token and cost budgets, preferred model, and whether governed fallback is permitted.

Model profiles are immutable evaluation-approved records containing capabilities, maximum supported risk, context size, cost, p95 latency, evaluation score and release, allowed data classes, provider, and circuit state. High-risk work has the strongest quality threshold. Open circuits, unsupported data, weak evaluation, missing capabilities, insufficient context, or budget/SLO violations make a model ineligible.

A preferred model is never silently substituted. Fallback requires an explicit hierarchy of at most two approved models and is recorded in the decision. When no governed model meets every constraint, the task escalates or uses the deterministic human-review fallback. Every selection fingerprints the request, budgets, selected model and evaluation release, fallback chain, and reason.
