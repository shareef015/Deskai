# DeskPilot AI ServiceOps

DeskPilot AI ServiceOps is a privately deployed, Windows-only IT service desk
for governed diagnosis and remediation of supported Microsoft Outlook, printer,
scanner, Windows service, and endpoint-connectivity incidents.

The product is designed around a non-negotiable lifecycle:

`ask -> consent -> diagnose -> explain -> authorize -> remediate -> verify -> user confirms -> close`

## Product boundary

- Managed endpoints: Windows 10 and Windows 11 only.
- Windows 10: full operation requires an eligible ESU enrollment or a supported
  LTSC lifecycle. Otherwise the device is placed in restricted-support mode.
- Windows 11: the edition and feature release must be within Microsoft's active
  servicing lifecycle.
- Private deployment: customer data remains within the customer-controlled
  environment, except for explicitly configured model/observability providers.
- No unrestricted remote shell, hidden remote control, credential extraction,
  or autonomous privileged administration.
- A successful command is not proof of resolution. Technical verification and
  employee confirmation are both required before closure.

## Repository map

```text
deskpilot-ai/
├── contracts/                 Machine-readable product contracts
├── docs/product/              Authoritative product and commercial scope
├── scripts/                   Contract validation utilities
└── tests/contracts/           Executable acceptance checks
```

## Validate

Python 3.11 or newer is required.

```bash
python scripts/validate_scope.py
python -m unittest discover -s tests -p 'test_*.py'
```

## Status

This repository currently establishes the authoritative scope and acceptance
contracts plus version-aware Outlook, printing, scanning, Windows and network
support catalogues with deterministic Windows 10/11 demo cases. Runtime
services will be added cumulatively without changing the single
`deskpilot-ai/` project root.

The project also defines human and machine authority boundaries, segregation
of duties, a 25-person synthetic demo tenant, and fail-closed environment
configuration with redacted release fingerprints.

Runtime credentials and endpoint certificates are governed through approved
secret-provider references, redacted value types, least-privilege service
identities, expiry enforcement and audited zero-downtime rotation.

Operational telemetry uses privacy-safe structured JSON events with end-to-end
correlation, recursive redaction, tenant pseudonymization, bounded retention and
explicit links to—not replacements for—immutable audit records.

All runtime boundaries share a stable typed error taxonomy. API failures return
correlation-aware, non-cacheable problem documents without exception messages,
stack traces, rejected values, secrets or internal paths.

Engineering changes are protected by matching local and CI quality gates:
Ruff, strict mypy, ESLint, TypeScript, contract tests, production builds, secret
scanning and dependency audits. Gate exceptions cannot be silent or permanent.

The PostgreSQL logical model now defines tenant-scoped identities, devices,
incidents, append-only history, evidence lineage, human authorization,
remediation, verification, durable AI execution and tamper-evident audit data.

SQLAlchemy 2 async repositories bind every query to a tenant and operate within
an explicit unit of work. Repositories flush without committing, transaction
owners roll back failures, and incident updates use optimistic versions.

Alembic exclusively owns schema changes through immutable, checksum-protected
revisions with transaction-scoped migration locking, drift detection and tested
upgrade/downgrade procedures.

Critical PostgreSQL access paths use tenant-leading, workload-aware indexes,
keyset pagination, bounded query limits, query-plan regression gates and
parameter-safe slow-query observability.

Tenant isolation is enforced across authenticated context, tenant-bound
repositories, transaction-local database context, forced PostgreSQL row-level
security and composite tenant foreign keys. The runtime role cannot bypass RLS.

Enterprise authentication uses OIDC authorization code with PKCE for people and
tenant-scoped OAuth client credentials for services. Access tokens require
asymmetric signatures, exact issuer/audience validation and an immutable tenant
claim before any tenant context is established.

Authorization uses tenant-scoped, time-bounded role assignments, scoped
resources, explicit deny precedence and independent segregation-of-duties rules.
Token role claims alone never authorize an operation.

The inventory models employees, Windows endpoints, printers, scanners and print
servers with privacy-safe identifiers, temporal assignment history, explicit
device lifecycle transitions and optimistic concurrency.

Redis provides tenant-separated reconstructible caching, AES-GCM encrypted
server-side sessions and token-safe bounded distributed locks. Durable business
state remains in PostgreSQL, and security-sensitive outages fail closed.

Material actions are recorded through a database-controlled, tenant-local audit
hash chain with immutable triggers and restricted append authority. Evidence
preserves source-to-derived lineage, integrity hashes, retention and legal hold.

Authenticated incident APIs provide tenant-scoped create, read, keyset-list and
version-checked update operations with strict schemas, authorization hooks and
no generic delete or lifecycle-state bypass.

Incident status now advances through a persistent guarded state machine. Each
accepted transition atomically increments the incident version and writes both
incident history and tamper-evident audit history in the same transaction.

Incident priority and severity are computed from bounded impact and urgency
signals by a versioned deterministic engine. Human overrides are authorized,
expiring, immutable and audited; clients and LLMs cannot set final priority.

Versioned SLA clocks apply continuous or tenant business-calendar targets,
preserve ownership and pause history, and emit deduplicated warning, breach and
unowned escalations without granting remediation or closure authority.

Typed, versioned incident events and their publication-ready outbox records are
written atomically. Event identity remains immutable while delivery metadata can
advance through bounded at-least-once publication and dead-letter handling.

Durable background jobs are transactionally enqueued, tenant-scoped, leased with
random owner tokens, retried with bounded jitter and preserved in immutable
attempt/dead-letter history.

Mutating APIs require tenant-scoped idempotency keys. Canonical request
fingerprints reject key reuse with different input, while matching duplicates
receive the original encrypted response without re-executing the operation.

Distributed API protection atomically applies weighted tenant, user and network
token buckets with pseudonymous Redis keys, safe limit headers and fail-closed
behavior for security-sensitive dependency outages.

Authenticated tenant-scoped SSE streams replay ordered incident activity from
durable history, emit bounded heartbeats, honor reconnect cursors and avoid
unbounded buffering under slow-client backpressure.

The public `/api/v1` contract uses deterministic OpenAPI generation, stable
operation IDs, compatibility gates and aligned Python and TypeScript clients.
Breaking changes require a new major API version and an explicit migration.

The demonstration tenant has a deterministic synthetic organization with
hierarchical departments, three locations and domain-specific support groups.
Its stable seed enables exact replay without real people or customer data.

The synthetic workforce adds reproducible manager relationships, support-group
membership, skills and shift coverage while keeping role authorization separate
from routing metadata.

Fictional Entra-compatible identities support a passwordless persona picker in
synthetic development and test environments only. Demo sessions are opaque,
server-side, CSRF-protected and cannot replace production OIDC authentication.

Ten reproducible Windows endpoint profiles model hardware, supported builds,
assigned employees, applications, security posture and baseline health while
preserving lifecycle restrictions and hashed-only serial identity.

Every lab endpoint includes a versioned synthetic inventory of applications,
Windows services, signed drivers, peripherals and explicit dependency health,
with expected state kept separate from scenario-observed state.

The synthetic network models private subnets, adapters, DHCP, gateways, DNS,
proxy, certificate Wi-Fi and VPN routing, plus explicit reversible fault states
without storing credentials, keys or customer network data.

The fictional Microsoft 365 environment separates classic and new Outlook,
mailbox metadata, profiles, cache, add-ins, authentication, connectivity and
sync health, with reversible failures and no messages or secret material.

The print and scan laboratory includes deterministic printers, scanners, print
servers, queues, ports, signed drivers, WIA/TWAIN state and permissions, with
privacy-safe verification and reversible failure injection.

The content-addressed digital twin unifies every synthetic domain, applies
version-checked faults, records deterministic replay journals, supports exact
rollback and restores the full tenant baseline on reset.

An authenticated non-production control panel exposes predefined scenarios,
state digests, snapshots, comparisons, rollback and confirmation-gated reset;
AI identities and arbitrary state mutations are denied.

The Outlook incident generator creates a canonical replay corpus spanning every
supported Outlook incident class, with evidence lineage, approvals, rollback,
verification and deterministic closure but no mailbox content or side effects.

The printer incident generator creates topology-linked replay cases for every
supported printer failure, enforcing metadata-only evidence, governed rollback,
and synthetic test-page plus physical-output confirmation before resolution.

The scanner incident generator covers WIA, TWAIN, USB, network and MFP failure
paths with temporary content-blind test-scan artifacts, approval, rollback and
employee confirmation before deterministic closure.

The Windows and network incident generator creates replayable, redacted cases
across connectivity, services, updates and resource pressure, requiring layered
diagnosis and original business-function verification rather than ping alone.

The conversation generator links every synthetic incident to a replayable
employee dialogue with a time-aware greeting, explicit scoped consent, separate
remediation approval, verification feedback and confirmation-gated closure.

Synthetic endpoint telemetry provides correlated, replayable Windows health and
typed diagnostic results with bounded timing, safe failures, redaction and
evidence lineage—without unrestricted commands or endpoint side effects.

The synthetic authorization corpus tests incident-scoped consent, independent
risk-based approval, rejection, expiry, revocation, mismatch and segregation of
duties; every invalid or machine-authorized decision fails closed.

Synthetic remediation scenarios model typed, authorized and idempotent repairs
through success, failure, timeout, compensation and digest-verified rollback,
with safe escalation whenever restoration cannot be proven.

The balanced regression corpus contains exactly 500 deterministic cases across
all support domains, scenario classes, incident taxonomies and endpoints, with
cross-artifact lineage and a byte-exact replay manifest.

Guided recruiter mode provides eight curated, operator-driven synthetic replays
for resolution, refusal, rejection, rollback and escalation, with deterministic
reset and no route to production endpoints.

The AI service now defines tenant-safe typed graph input, internal and output
state with bounded deterministic reducers for parallel messages, evidence,
errors and retries plus explicit consent, approval and execution validation.

Durable graph execution uses encrypted asynchronous PostgreSQL checkpoints with
tenant-scoped opaque threads, pending-write recovery, optimistic checkpoint
heads, configuration-bound replay and legal-hold-aware retention.

Durable graph interrupts now separate diagnostic consent, remediation approval
and employee confirmation, accepting only authenticated, scoped, unexpired and
idempotent server-validated resume decisions.

Authenticated resume, replay and fork controls now bind checkpoint digest and
configuration, preserve immutable history, migrate state through an explicit
version registry and require fresh human decisions before replayed side effects.

The master service-desk supervisor coordinates the complete Windows support
journey through explicit bounded routes. Consent, policy authorization, narrow
capability tokens, technical verification and employee confirmation are hard
gates; missing or unsafe conditions fail closed to human escalation.

Conditional domain routing deterministically selects Outlook, printer, scanner
or Windows/network specialists from scored evidence. Confidence and margin
gates, bounded multi-domain fan-out, clarification limits and auditable route
fingerprints prevent silent or unsupported routing.

Domain specialists run as isolated, bounded nested graphs with typed inputs and
evidence-only outputs. Domain-specific read-only tool allowlists and supervisor-
owned lifecycle authority prevent specialists from approving, remediating or
closing incidents.

Bounded parallel diagnostics can fan out to two read-only specialists. The
convergence reducer deterministically merges scoped evidence, removes exact
duplicates, preserves contradictions and retains safe partial results when a
branch fails or times out.

Per-node resilience enforces deadlines, classified bounded retries, durable
circuit-breaker transitions and one idempotent compensation attempt after a
partial mutation. Authorization and policy failures never retry, and unsafe
recovery paths escalate with secret-safe provenance.

Deterministic termination guards every graph edge with reasoning, step, visit,
cycle and progress limits. Unsafe or weakly grounded paths abstain to human
escalation, terminal states are immutable, and every ending carries a
machine-verifiable path proof.

Prompts and agent policies are immutable, versioned registry artifacts with
exact schema and tool compatibility, independent approval, evaluation-gated
release fingerprints, capped canaries and append-only rollback provenance.

The employee conversation supervisor provides local-time greetings, accessible
bounded clarification, explicit read-only consent language, intent continuity
and transparent escalation without diagnostic, approval or remediation tools.

The incident-intake extractor produces strict, source-traceable symptoms,
impact, registered device, timeline, domain candidates and uncertainty fields.
It redacts secret-like input and routes incomplete records to clarification
without diagnosing or inventing facts.

Context-aware clarification selects at most two high-information questions from
explicit gaps and contradictions, preserves answered context, never repeats a
question identifier and escalates safely after three unresolved rounds.

Employee-device resolution matches only active tenant-scoped relationships to
registered Windows 10/11 devices, limits disclosed metadata, handles ambiguity
and requires an explicit scope-bound confirmation before diagnostic consent.

The advanced Outlook specialist separates classic and new Outlook, plans only
consented read-only diagnostics, issues version-filtered RAG queries, grounds
hypotheses in evidence and returns risk-rated, rollback-aware proposals for
independent approval and later verification.

The printer/scanner specialist uses topology-aware read-only evidence across
queues, spooler, ports, print servers, WIA, TWAIN and reachability, preserves
Windows Protected Print Mode, and requires real test-print or safe test-scan
confirmation before resolution.

The Windows/network specialist follows a layered, consented diagnostic path
across services, processes, bounded Event Logs, resource pressure, Windows
Update, adapters, DHCP, DNS, proxy, VPN, routes and target ports. Firewall and
security state is read-only; remediation remains a rollback-aware proposal and
resolution requires the original business function plus employee confirmation.

The evidence-fusion agent deterministically correlates scoped specialist,
telemetry, inventory, employee and RAG evidence. It requires independent source
support, preserves contradictions and close competing causes, and advances only
a threshold-qualified root cause while retaining complete evidence provenance.

The remediation planner converts only a grounded cause into a minimal typed
change plan. It classifies risk and blast radius, requires qualified approval,
pre-state, rollback, idempotency and end-to-end verification, and has no
approval, tool-execution or closure authority.

An independent remediation critic checks the immutable plan for evidence,
capability, risk, blast-radius, rollback, idempotency, approval, segregation-of-
duties and verification defects. It passes, returns for revision or escalates,
but cannot rewrite, approve or execute the plan.

Human approval packets bind the exact critic-passed plan, tenant, incident,
device, checkpoint, risk and capability scope. Authenticated risk-qualified
decisions enforce expiry, revocation, segregation of duties, immutable plan
fingerprints and idempotent replay before execution can be considered.

Governed execution exchanges exact human approval for a five-minute signed
capability token. The gateway accepts only allowlisted typed actions with
bounded parameters, pre-state, rollback, idempotency and deadlines; raw command
execution is structurally unavailable and partial failures route safely.

Outcome verification compares bounded read-only post-state evidence against the
expected technical state and original business function, checks regressions,
and routes failures to rollback. Resolution additionally requires authenticated
confirmation from the employee assigned to the affected device.

Closure requires the complete root-cause-to-verification provenance chain and
creates a bounded redacted resolution record. Reusable knowledge remains an
evidence-linked candidate pending human curation; recurrence reopens diagnosis
instead of silently reusing the prior closure.

Escalation creates a severity- and SLA-aware evidence packet for a deterministic
human owning team. Hop limits prevent circular routing, acknowledgement requires
an authenticated team member, and human remediation returns to verification
with new evidence rather than bypassing closure gates.

Privacy-safe agent observability hash-chains every correlated graph, agent,
retrieval, tool, human, retry, error, budget and terminal event. It records
fingerprints, versions, evidence IDs, cost and latency—not raw private content—
and links operational traces to the separate immutable audit ledger.

The production agent evaluation harness scores all 500 deterministic cases at
aggregate and domain/scenario-slice levels. Safety, tenant isolation, approval
enforcement and replay determinism are zero-tolerance release gates alongside
governed accuracy, latency and cost thresholds.

The adversarial red-team suite exercises 150 deterministic injection, poisoning,
isolation, authorization, capability, tampering, replay, leakage, exhaustion and
false-resolution attacks. Every family has a 100-percent defense requirement;
one unsafe result blocks release.

Online monitoring compares tenant-safe trace aggregates with approved model,
prompt, configuration and quality baselines. Critical safety or fingerprint
drift freezes automated execution and routes traffic to deterministic triage and
human review; noncritical degradation increases review and alerts operators.

Quality-aware routing selects only evaluation-approved models that satisfy task
risk, capability, data-class, context, token, cost, latency and circuit-state
constraints. Fallback uses an explicit two-model hierarchy; silent model
substitution is prohibited and every decision is fingerprinted.

Tenant-safe caching binds prompt, embedding, retrieval and eligible response
entries to tenant and exact model, prompt, configuration, index and policy
releases. Similarity and grounding are revalidated, sensitive classes are
encrypted, and all high-risk or approval/execution/verification paths bypass.

Deterministic context compression activates before token-budget exhaustion while
pinning scope, consent, approval, evidence, contradictions, plan, rollback,
verification, human decisions and audit lineage. Source hashes and freshness
must match exactly before a compressed history can be rehydrated.

The prompt firewall labels instruction trust, treats retrieval, endpoint and tool
content as isolated data, detects injection and secret requests, and permits only
bounded typed tool arguments. Cross-tenant or tampered content and any raw
command surface fail closed with security-decision provenance.

Memory governance separates incident working state, consented episodic continuity
and human-curated reusable knowledge. Tenant, subject, incident, purpose, TTL,
encryption, provenance, conflict handling and deletion are enforced; hidden or
automatic cross-incident model memory is prohibited.

Planning governance admits only approved objectives and bounded acyclic step
graphs with evidence, tool, token and time contracts. Plans and at most two
replans are immutable and fingerprinted; the exact version must pass an
independent critic before orchestration.

Delegation governance gives each specialist a typed, scoped, budgeted task with
capabilities strictly below the parent, two-level depth and two-child fan-out.
Human authority never transfers, and child evidence, resources, cancellation,
schema and provenance are validated before any result is accepted.

The capability registry versions every typed tool and maps agents to exact
minimum grants. Tenant, incident, device, consent, approval, rate and parameter
predicates are rechecked per call; dynamic tools, wildcard grants and raw command
arguments are unavailable, and every decision is audit-fingerprinted.

Governed MCP dispatch signs a two-minute, single-use envelope for the authorized
tenant/device capability and verifies endpoint certificate, attestation, build,
policy and health. Typed signed results preserve evidence lineage; replay,
tampering, raw content or drift causes denial and endpoint quarantine.

End-to-end integration validates the complete greeting-to-closure graph, every
agent and governance module, all four support domains, rollback and escalation
paths, terminal behavior and required safety-gate order. Orphans, missing modules,
contract drift or scenario failures block readiness.

The real-time runtime API provides idempotent tenant-scoped start, validated
resume, cancel and cursor-reconnect event streaming. Operator events expose only
privacy-safe lifecycle metadata, terminal runs are immutable, and recruiter demo
controls remain isolated from live endpoint authority.

The human-interrupt inbox separates employee consent and confirmation from
qualified remediation approval. Review packets are privacy-safe, decisions are
tenant-, actor- and checkpoint-bound, self-approval is denied, and expiry,
revocation, idempotency and live reconnect cursors fail closed.

The incident workspace presents the governed support journey as a typed,
accessible and responsive UI. It reconnects from durable event cursors, rejects
unapproved event fields, bounds timeline history, uses real decision forms and
keeps recruiter demonstrations visibly isolated from live tenant operation.

Conversation streaming provides idempotent employee messages, bounded typed
assistant deltas, secret redaction, cursor recovery and immediate stop handling.
Attachments stay disabled, and accessible consent-aware controls keep chat
separate from diagnostic or remediation authority.

The evidence explorer exposes immutable digest-verified observations through
safe summaries, derived freshness, preserved contradictions and complete
specialist-to-supervisor lineage. Technical details are allowlisted and exports
are role-scoped, tenant-hashed and deterministically fingerprinted.

Remediation review binds independent approval to an immutable action graph,
checkpoint and plan fingerprint. Reviewers see dependencies, risk, before/after
state, rollback and verification; expiry and self-approval fail closed, while
partial failure routes deterministically to rollback or human recovery.

Execution uses a single-use, exact-capability token bound to the approved plan
and signed pre-state. Immutable action results drive verification, rollback or
human recovery, and closure requires complete regression checks plus the
employee's explicit confirmation that the original function works.

Human escalation uses privacy-safe digest-bound packets, tenant team queues,
computed SLA state and authenticated single-owner custody. Human changes are
fingerprinted and must return through governed technical and employee
verification; immutable custody history preserves every transfer.

Incident closure requires complete technical and employee verification, a safe
summary and evidence references. Immutable records capture SLA outcome and
audit provenance; knowledge publication remains a separate human decision, and
reopen preserves closure while requiring a governed reason and regression evidence.

Knowledge publishing de-identifies closure-derived candidates, enforces
provenance, duplicate and quality gates, and requires independent technical
approval. Immutable tenant-scoped versions drive fingerprinted RAG index
refresh; retirement and rollback preserve the complete publication history.

The operations dashboard provides tenant- and environment-isolated incident
queues with deterministic severity/SLA priority, derived aging and stalled-run
signals, approval backlog, rollback alerts and reconnect-safe live cursors.
Recruiter synthetic metrics remain visibly and technically separate from live data.

Agent observability exposes privacy-safe graph spans with node latency, routing,
model tokens/cost, tool decisions, retry/circuit state, governed quality,
drift and SLO alerts. Tenant and environment filters prevent live telemetry
from mixing with synthetic recruiter traces.

Evaluation gates compare immutable evidence-bound candidate runs with scoped
baselines across domain and scenario slices. Quality thresholds and regression
budgets classify blockers; only an independent approver can release an eligible
exact run, while synthetic recruiter evaluations stay isolated from live evidence.

AI release management binds prompt, agent policy, model profile, graph and
schema versions to approved evaluation evidence. Independent approval, separate
environment assignments, bounded canaries, approved rollback and emergency
freeze produce append-only deployment provenance.

Authentication uses OIDC issuer and audience validation with tenant-, role-,
mode- and expiry-bound server sessions. Recruiter personas are short-lived,
synthetic-only, non-production identities; secure logout, live-impersonation
denial and hashed audit events preserve access provenance.

The application shell provides tenant- and mode-visible, role-filtered grouped
navigation with an accessible responsive drawer and breadcrumbs. Shared loading,
error and empty states keep support workflows understandable without exposing
unauthorized destinations or implementation-phase terminology.

Governed action surfaces replace browser prompts and alerts with typed forms,
accessible confirmation dialogs and responsive drawers. Server validation binds
every submission to its tenant, incident, actor role and action fingerprint while
rejecting stale, duplicate, oversized or secret-like payloads.

Advanced Investigation consolidates evidence graphs, retrieval provenance, agent
traces and specialist summaries behind consent and investigator roles. A route
ownership validator prevents incomplete or orphaned pages from entering the
recruiter demo or production navigation.

Frontend contracts parse unknown data into versioned strict view models before
rendering. Unified theme tokens and quality checks enforce semantic landmarks,
live announcements, visible focus, contrast, interaction targets, reduced motion,
forced-color compatibility and responsive layouts.

The employee conversation now remains continuous through visible follow-up
questions, registered-device confirmation, scoped remote-access permission,
UI-mode diagnostics, separate repair approval, technical verification and
employee confirmation. Decline, revocation and failed verification remain safe
continuation or escalation paths instead of false resolution.

The accepted architecture uses web, API, LangGraph AI, RAG, MCP gateway and
worker boundaries with PostgreSQL durable state, Redis acceleration and a
signed mutual-TLS Windows endpoint agent.

## Ownership

Proprietary. All rights reserved. See `LICENSE`.
