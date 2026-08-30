# ADR: Governed Endpoint Agent

Status: accepted.

Use a signed Windows service with mutual TLS and typed capabilities. Do not
expose arbitrary PowerShell, remote shell or direct AI-to-endpoint access. The
endpoint verifies machine, tenant, incident, expiry, arguments and replay
protection locally.
