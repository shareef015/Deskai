# DeskPilot AI staging overlay

This directory is a production-like Kubernetes baseline, not a provider-complete cluster definition. Before use:

- replace `registry.example.invalid` images with immutable signed image digests;
- replace `deskpilot-staging.example.invalid` with staging DNS;
- provide `deskpilot-runtime-secrets` through KMS/Vault/External Secrets;
- add provider-specific egress destinations to the default-deny NetworkPolicy;
- verify `/healthz`, `/readyz` and frontend `/api/health` routes match the integrated application;
- configure ingress-controller-specific TLS/streaming annotations as required;
- validate all manifests with your cluster version and admission policies.

`runtime-secrets.example.yaml` is documentation only and is intentionally not referenced by `kustomization.yaml`.
