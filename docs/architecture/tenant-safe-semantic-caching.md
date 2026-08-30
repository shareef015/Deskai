# Tenant-Safe Semantic Caching and Cost Optimization

Cache keys bind tenant, cache class, task stage, risk, data class, exact model release, prompt, configuration, index, policy, and normalized input fingerprints. A hit therefore cannot cross tenants or survive a model, prompt, policy, configuration, or index release change.

Prompt, embedding, retrieval, and eligible response entries use class-specific TTLs. Retrieval and response hits require both semantic similarity and live grounding-fingerprint revalidation. Sensitive cache classes must be encrypted; sensitive responses are not cached. Fill leases prevent stampedes, while validated hits record cost savings without exposing cached content.

High-risk reasoning and evidence fusion, remediation planning, approval, execution, verification, closure, and escalation always bypass semantic response reuse. Expired, below-threshold, changed-grounding, or release-mismatched entries are misses or invalidations rather than stale answers. Cache optimization can reduce latency and cost but never relax tenant, evidence, approval, or safety boundaries.
