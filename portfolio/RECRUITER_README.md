# DeskPilot AI — Recruiter Portfolio Package

DeskPilot AI is a production-oriented AI service-desk platform focused on synthetic Windows Outlook and Printer incidents.

The recruiter demo is intentionally separated from production. It demonstrates:

- service-desk greeting and incident intake
- governed RAG and citation grounding
- LangGraph-style deterministic agent orchestration
- read-only diagnostics before remediation
- HITL approval for mutating actions
- controlled MCP-style remediation
- independent verification before closure
- tenant isolation, audit, observability, quality, performance and security gates

## Safety boundary
This portfolio package must contain only synthetic/de-identified demo data. Production credentials, real customer identifiers, internal hostnames, private evidence URLs, secrets and raw production traces are prohibited.

## Recommended demo path
1. Open the synthetic recruiter demo workspace.
2. Choose Printer Queue Stuck or Outlook Disconnected.
3. Show the greeting and intake flow.
4. Show RAG evidence/citations.
5. Show agent routing and read-only diagnostics.
6. Show the remediation plan and HITL approval.
7. Run the simulated controlled remediation.
8. Show independent verification and closure.
9. Reset the deterministic demo environment.
