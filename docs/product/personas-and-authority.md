# Personas and Authority Boundaries

## Human roles

Employees own consent for incident-specific access to their assigned device and
confirm whether the business function works. Consent does not give them power
to authorize enterprise identity, network, security or privileged endpoint
changes.

Service-desk engineers collect evidence and propose bounded repair. L2/L3
specialists handle complex escalations. Medium-risk changes use an independent
remediation approver. High-risk changes route to the administrator who owns the
affected domain: endpoint, network, identity/Exchange or security.

Tenant administrators configure customer policy and role assignments but
cannot alter audit history. Auditors are read-only and cannot decide approvals,
execute tools or publish policy.

## AI authority

The AI service may classify, retrieve, reason, recommend and propose a typed
tool request. It cannot grant consent, approve remediation, expand its own
permissions, issue a capability token or decide that a person has authority.
Those decisions are made by authenticated humans and deterministic policy.

## Segregation of duties

- A medium- or high-risk proposer cannot be the sole approver.
- High-risk changes require the matching domain administrator.
- An auditor cannot modify operational records.
- Employee consent is limited to the correct tenant, incident and assigned or
  explicitly delegated device.
- Break-glass access is disabled by default, time-limited, human-only and
  requires post-event review.

## Synthetic identities

The demo tenant contains 25 fictional identities covering employees and every
authority role. Names, departments, assignments and devices are synthetic.
They provide reproducible recruiter demonstrations without using real people or
customer data.
