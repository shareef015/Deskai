# Windows-Only Product Scope

## Purpose

DeskPilot AI ServiceOps provides conversational L1/L2 assistance, governed
endpoint diagnostics, evidence-grounded troubleshooting, authorized repair and
verified incident closure for privately managed Windows endpoints.

## Supported endpoints

The product enrolls Windows 10 and Windows 11 employee endpoints only. Enrollment
must capture the edition, feature release, build, architecture, update status,
tenant, employee assignment and machine identity.

Windows 10 reached general end of support on 14 October 2025. Full live
remediation is therefore restricted to devices with verified enterprise ESU or
a supported LTSC lifecycle. Other Windows 10 devices may receive restricted
diagnostics and migration guidance under customer policy.

Windows 11 support is feature-release and edition specific. The platform must
refresh lifecycle information from Microsoft and fail safely when that
information becomes stale.

## Supported service-desk domains

1. Outlook for Windows: startup, performance, connection, authentication,
   send/receive, cache, OST, add-ins, profiles, search, shared mailbox and
   calendar synchronization problems.
2. Printing: discovery, offline state, queues, jobs, spooler, drivers, ports,
   print servers, network reachability, mappings and defaults.
3. Scanning: discovery, WIA, TWAIN/WIA drivers, applications, network scanners
   and access permissions.
4. Supporting Windows connectivity: approved DNS, proxy, VPN, network adapter,
   service and endpoint-agent checks needed to investigate the three primary
   domains.

## Consent and remediation boundary

Endpoint access is never implied by beginning a chat. DeskPilot must identify
the employee and device and obtain incident-specific diagnostic consent before
creating an endpoint session. Diagnostic consent grants read-only capabilities
by default.

A proposed change is explained in plain language. Remediation authorization is
separate and action-specific. Medium- and high-risk actions follow customer
approval policy and segregation of duties. The LLM proposes; deterministic
policy code authorizes.

## Closure invariant

An incident cannot enter `RESOLVED` until the repair has been technically
verified and the employee has confirmed that the business function works. A
tool exit code alone is never sufficient.

## Private deployment

Application data is customer-controlled. Integrations that send prompts,
retrieval context, traces or telemetry outside that boundary are disabled by
default and require explicit customer configuration, contractual approval,
redaction and audit logging.

## Explicit exclusions

- Non-Windows managed endpoints.
- Windows Server as an employee workstation target.
- Arbitrary shell or arbitrary PowerShell execution.
- Hidden, persistent or cross-tenant remote access.
- Password, token or secret extraction.
- Autonomous identity, Conditional Access, Exchange transport or security-policy
  administration.
- Physical repair of printers, scanners or computers.
- Guaranteed resolution where evidence, permission or supported remediation is
  unavailable.
