# Outlook for Windows Support Catalogue

## Operating principle

DeskPilot diagnoses Outlook as an evidence hierarchy, not a list of random
fixes. It first determines whether the employee uses classic Outlook
(`outlook.exe`) or new Outlook (`olk.exe`). Client-specific capabilities are
then applied so classic profile, COM add-in, OST and Windows Search procedures
are not incorrectly applied to new Outlook.

## Investigation order

1. Confirm employee, device, Windows lifecycle and Outlook client.
2. Capture the exact symptom, error code, scope and last-known-good time.
3. Check whether multiple employees are affected and inspect service health.
4. Compare Outlook desktop behavior with Outlook on the web where permitted.
5. Collect read-only process, event, network, sync and configuration evidence.
6. Use version-matched approved knowledge.
7. Rank root-cause hypotheses and request more evidence when confidence is low.
8. Explain a reversible remediation and request the required authorization.
9. Capture pre-state, execute a typed action and collect post-state.
10. Verify connection/synchronization and perform a send/receive test.
11. Ask the employee to confirm the business function works.

## Safety boundaries

- Safe mode is a diagnostic for classic Outlook; it is not treated as a repair.
- An add-in is disabled only when evidence connects it to the failure.
- An OST is recreated only after confirming the authoritative server copy and
  considering unsynchronized local items.
- A PST repair requires a backup and explicit approval because it can affect
  the only local copy of data.
- A replacement profile is created and tested in parallel before changing the
  default. Deletion of the previous profile is high risk.
- Identity, MFA, Conditional Access, Exchange permissions, mailbox delegation
  and mail-flow changes require a privileged administrator.
- Content of email messages is not collected for routine diagnosis.

## Escalation

DeskPilot escalates security indicators, tenant-wide impact, service outages,
privileged tenant changes, potential data loss, unsupported builds, unresolved
contradictions and incidents that exceed the bounded diagnostic budget.

The escalation package includes the conversation summary, device/client build,
consent record, diagnostic evidence, attempted actions, before/after state,
ranked hypotheses, citations and recommended next human action.
