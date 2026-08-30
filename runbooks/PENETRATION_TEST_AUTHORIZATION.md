# Authorized Staging Penetration Test Boundary

Connected staging requires evidence from an authorized staging security assessment. The included project does not authorize testing of any third-party, production, employee or customer system.

The written authorization should identify the exact staging hostnames/IP ranges, test window, permitted identities, allowed test categories, excluded destructive techniques, rate limits, data-handling rules, emergency contacts and stop conditions. Use synthetic data and staging-only devices. Do not run destructive denial-of-service, persistence, credential harvesting or lateral movement outside the explicitly approved scope.

Expected evidence for the Connected staging gate is a signed/approved report or ticket reference plus an immutable fingerprint and remediation status for any critical/high findings.
