# Acceptance Criteria

## Scope contracts

- The product contract names only Windows 10 and Windows 11 managed endpoints.
- Unsupported platforms are explicitly rejected.
- Windows 10 full operation requires ESU or supported LTSC status.
- Windows 11 support is tied to the Microsoft lifecycle for its edition and
  feature release.
- Outlook, printer, scanner and supporting Windows-connectivity incident classes
  have explicit supported and escalation boundaries.

## Access and safety

- Diagnostic consent precedes endpoint-session creation.
- Diagnostic consent is incident-, employee-, device- and tenant-specific.
- Remediation authorization is separate and action-specific.
- The LLM cannot grant authorization.
- Consent expires and can be revoked.
- Unrestricted shells, credential extraction and cross-tenant execution are
  prohibited.

## Resolution

- Technical verification is required after remediation.
- Employee confirmation is required after technical verification.
- Failures produce evidence and escalation rather than false success.

## Commercial and privacy boundary

- The software is proprietary and privately deployed.
- License/device limits are enforced outside the LLM.
- External data transfer is denied by default.
- Synthetic demonstration mode uses no real employee or company data.

## Executable evidence

`python scripts/validate_scope.py` and the contract test suite must pass. The
release archive must contain one top-level directory named `deskpilot-ai`.
