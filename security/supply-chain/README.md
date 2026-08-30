# Supply-chain certification contract

Security statically checks the packaged artifact for high-risk dependency and secret-material issues.

Release requirements in connected CI/staging:

- exact runtime dependency versions;
- committed resolver-generated lockfiles;
- `npm audit`/registry advisory scanning;
- Python dependency vulnerability scanning;
- SBOM generation and artifact attestation;
- no private keys, production `.env` files or embedded credentials;
- dependency update PRs reviewed through the existing Dependabot workflow;
- build provenance retained with the release candidate.

The local artifact does not invent a lockfile when registry resolution cannot complete. Missing resolver-generated lockfiles remain visible as a deployment warning.
