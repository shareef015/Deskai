# Scope Validation Report

Validation date: 2026-08-25

## Results

- Machine-readable scope validator: passed.
- Automated contract and unit tests: 60 passed, 0 failed.
- Managed endpoint scope: Windows 10 and Windows 11 only.
- Initial real-device pilot boundary: 10 endpoints.
- Diagnostic consent requirement: enforced by contract.
- Separate remediation authorization: enforced by contract.
- Technical verification and employee confirmation: required by contract.
- External data transfer default: denied.
- Outlook catalogue: 11 incident classes validated.
- Outlook demo data: 10 deterministic scenarios across Windows 10 and 11.
- Classic and new Outlook client boundaries: validated.
- High-risk Outlook actions: human approval required.
- Printer catalogue: 11 incident classes validated.
- Printer demo data: 10 deterministic scenarios across Windows 10 and 11.
- Test-print and physical-output confirmation: required for every printer case.
- Protected Print Mode and privileged driver changes: human authority required.
- Scanner catalogue: 10 incident classes validated.
- Scanner demo data: 10 deterministic scenarios across Windows 10 and 11.
- Controlled synthetic test scan and employee confirmation: universally required.
- Diagnostic use of employee documents: prohibited.
- Windows/network catalogue: 12 incident classes validated.
- Windows/network demo data: 10 deterministic scenarios across Windows 10 and 11.
- Original business-function verification: required for every network case.
- Firewall/EDR disable, secret extraction and automatic network reset: prohibited.
- Human authority roles: 10 validated.
- Synthetic personas: 25 unique identities validated.
- AI approval and break-glass authority: prohibited.
- Segregation of duties and read-only auditor boundaries: validated.
- End-to-end employee journey, gates, bounded retries and failure paths: validated.
- Functional requirements: 18 stable contracts and 8 complete use cases validated.
- SLO, quality KPI, security, retention and budget contracts: validated.
- System components, trust zones, data authority, flows and architecture ADRs: validated.
- Monorepo deployable boundaries, shared packages and operational roots: validated.
- Strict Python packaging, identifiers, UTC clock and explicit result primitive: validated.
- FastAPI factory, bounded dependencies, health probes and correlation middleware: validated.
- Strict Next.js client, accessible intake, permission language and health route: validated.
- OpenAPI 3.1 source contract plus strict Python schemas and typed TypeScript client: validated.

## Commands

```bash
python scripts/validate_scope.py
python scripts/validate_outlook_catalog.py
python scripts/validate_printer_catalog.py
python scripts/validate_scanner_catalog.py
python scripts/validate_windows_network_catalog.py
python scripts/validate_personas.py
python scripts/validate_employee_journey.py
python scripts/validate_functional_requirements.py
python scripts/validate_nonfunctional_requirements.py
python scripts/validate_architecture.py
python scripts/validate_repository_structure.py
python scripts/validate_python_foundation.py
python scripts/validate_api_foundation.py
python scripts/validate_web_foundation.py
python scripts/validate_shared_schemas.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

This report validates the product-scope contracts only. Runtime, endpoint and
end-to-end validation will be added as their corresponding capabilities are
implemented.
