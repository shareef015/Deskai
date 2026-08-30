# Governed MCP Dispatch, Endpoint Attestation, and Result Validation

MCP dispatch begins only after tool-registry authorization. A two-minute signed envelope binds tenant, incident, device, endpoint agent, exact tool version, capability, typed parameters, plan when applicable, authorization fingerprint, nonce, issue time, and expiry.

The gateway verifies the endpoint’s tenant/device identity, certificate fingerprint, attestation, approved agent build, policy fingerprint, and healthy status before dispatch. Degraded, drifted, unsigned, or quarantined agents receive no work. Nonces are single-use and expired or replayed envelopes fail closed.

Results must match the exact envelope scope and tool version, use allowlisted bounded scalar fields, contain no raw content, carry evidence IDs and result fingerprint, and have a valid signature. Authorization, envelope, result, and evidence fingerprints form one lineage. Tampering or policy noncompliance produces an auditable quarantine decision instead of trusting the endpoint.
