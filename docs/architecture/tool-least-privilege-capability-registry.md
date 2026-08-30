# Tool Least-Privilege and Capability-Registry Enforcement

Every tool is an immutable registry entry with ID, semantic version, capability, risk, allowed and required parameter keys, rate limit, consent and approval predicates, and registry fingerprint. Dynamic runtime tools and wildcard schemas are prohibited.

Each agent receives a tenant-scoped minimum grant listing exact capabilities and `tool@version` identities. Authorization binds tenant, agent, incident, device, capability, schema version, live call count, consent, and—when state changes—approval for the exact plan fingerprint. A grant never implies human authority.

Parameters must be bounded scalar values whose keys exactly satisfy the tool schema. Command, script, shell, PowerShell, raw input, authorization, credential, password, secret, and token fields are structurally denied. Every allow or deny decision fingerprints scope, registry version, grant, sanitized parameters, outcome, and reason for audit and deterministic replay.
