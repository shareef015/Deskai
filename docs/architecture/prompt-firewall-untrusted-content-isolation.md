# Prompt Firewall and Untrusted-Content Isolation

Every content block carries a tenant, source label, stable ID, size bound, and content fingerprint. Instruction precedence is system, policy, authenticated user, tool result, retrieved content, and endpoint content. Retrieved documents, endpoint strings, and tool output are always represented as untrusted data and never promoted into instructions.

The firewall detects attempts to override earlier instructions, reveal hidden prompts, impersonate administrators, execute shell or PowerShell, or request credentials, tokens, keys, and secrets. Attacks in untrusted data are quarantined and fingerprinted; prohibited authenticated requests are blocked. Cross-tenant, oversized, or tampered blocks fail closed.

Tool arguments pass a per-capability key allowlist and accept only bounded scalar values. Command, script, shell, PowerShell, authorization, credential, password, secret, and token fields are structurally rejected. The resulting allow, isolate, or block decision records trusted instruction fingerprints, isolated-data fingerprints, detections, sanitized arguments, and deterministic provenance.
