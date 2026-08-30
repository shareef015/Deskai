# Online Agent Quality, Drift, and Safety Monitoring

The monitor evaluates tenant-scoped windows of privacy-safe trace aggregates rather than raw conversations or endpoint output. Every window binds its trace-chain head and the active model, prompt, and configuration fingerprints to an independently approved baseline.

Quality signals include grounding, appropriate abstention, verification success, recurrence, errors, p95 latency, average cost, and statistical movement from the approved baseline. Consent bypass, approval bypass, tenant-scope violation, unsafe tools, false resolution, and protected-data disclosure are zero-tolerance metrics. Unapproved model, prompt, or configuration fingerprints are also critical drift.

Healthy windows continue normally. Noncritical quality or SLO degradation increases human review and emits alerts. Critical safety or configuration drift routes affected traffic to deterministic triage and human review while freezing automated remediation execution. The monitor cannot inspect raw private content, silently change policy, promote a model, or suppress a critical alert.
