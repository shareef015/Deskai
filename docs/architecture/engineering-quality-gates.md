# Engineering quality gates

Every change must pass the same deterministic checks locally and in CI. Pull
requests and pushes to the protected default branch run contract tests, Ruff,
strict mypy, ESLint, TypeScript, the production web build, secret detection,
and dependency audits. CI has read-only repository permissions and cancels
superseded runs.

Security checks are fail-closed. Gitleaks scans full history, dependency review
examines pull-request changes, and Python and JavaScript production dependencies
are audited. Exceptions require a named owner, security approval, a documented
rationale and an expiry; silent bypasses are prohibited.

Developer hooks provide fast feedback but do not replace CI. Branch protection
must require all jobs defined by the machine-readable quality policy before
merge.
