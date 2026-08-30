# DeskPilot AI Interview Talk Track

## Business problem
IT service desks repeatedly diagnose Outlook and printer issues using fragmented knowledge, manual checks and inconsistent remediation.

## Solution
DeskPilot AI combines governed retrieval, deterministic agent orchestration, controlled diagnostic/remediation tools and human approval to shorten diagnosis while preserving auditability and safety.

## Architecture story
Frontend → authenticated FastAPI boundary → tenant-safe RAG → evidence/citation validation → deterministic agent routing → MCP diagnostics → remediation plan → HITL approval → controlled remediation → independent verification → closure.

## Production engineering story
The project includes strict frontend contracts, identity and tenant isolation, backend/API security, observability/evaluation, capacity testing, adversarial testing, recruiter-demo certification, connected-staging gates and a fail-closed production promotion gate.

## Important claim discipline
The downloadable package implements production-grade controls and deterministic certification harnesses. It must not be described as production-deployed until connected Connected staging evidence and Production production acceptance are actually completed.
