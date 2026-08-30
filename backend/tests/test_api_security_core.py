from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_api_security.mass_assignment import FieldPolicy, MassAssignmentViolation, accept_fields
from deskpilot_api_security.rate_limit import TokenBucketLimiter
from deskpilot_api_security.repository import TenantRecord, TenantScopedRepository
from deskpilot_api_security.request_validation import RequestLimits, RequestValidationError, validate_request_id
from deskpilot_api_security.secrets import SecretConfigurationError, SecretRef, reject_inline_secrets
from deskpilot_api_security.service_identity import ServiceIdentityError, ServicePrincipal, ServiceTrustPolicy
from deskpilot_api_security.ssrf import SsrfPolicy, SsrfViolation
from deskpilot_api_security.tenant import TenantContext, TenantGuard, TenantViolation


class TenantIsolationTests(unittest.TestCase):
    def test_repository_never_returns_cross_tenant_object(self) -> None:
        repo = TenantScopedRepository([
            TenantRecord("a-1", "tenant-a", {"title": "A"}),
            TenantRecord("b-1", "tenant-b", {"title": "B"}),
        ])
        ctx = TenantContext("tenant-a", "user-a")
        self.assertEqual(repo.get(ctx, "a-1").id, "a-1")  # type: ignore[union-attr]
        self.assertIsNone(repo.get(ctx, "b-1"))
        self.assertEqual([row.id for row in repo.list(ctx)], ["a-1"])

    def test_tenant_id_cannot_be_mutated_by_update(self) -> None:
        repo = TenantScopedRepository([TenantRecord("a-1", "tenant-a", {"status": "new"})])
        ctx = TenantContext("tenant-a", "u")
        row = repo.update_payload(ctx, "a-1", {"status": "resolved", "tenant_id": "tenant-b"})
        self.assertEqual(row.tenant_id, "tenant-a")

    def test_generic_guard_denies_cross_tenant_even_for_platform_context(self) -> None:
        with self.assertRaises(TenantViolation):
            TenantGuard.require_same_tenant(TenantContext("a", "root", platform_admin=True), "b")


class MassAssignmentTests(unittest.TestCase):
    def test_unknown_and_immutable_fields_are_rejected(self) -> None:
        policy = FieldPolicy.from_allowed({"title", "status"})
        with self.assertRaises(MassAssignmentViolation):
            accept_fields({"title": "ok", "tenant_id": "attacker"}, policy)
        with self.assertRaises(MassAssignmentViolation):
            accept_fields({"title": "ok", "is_admin": True}, policy)


class SsrfTests(unittest.TestCase):
    def test_blocks_metadata_private_loopback_and_non_https(self) -> None:
        policy = SsrfPolicy()
        private_cases = [
            ("https://metadata.example/", ["169.254.169.254"]),
            ("https://internal.example/", ["10.1.2.3"]),
            ("https://loopback.example/", ["127.0.0.1"]),
        ]
        for url, ips in private_cases:
            with self.subTest(url=url), self.assertRaises(SsrfViolation):
                policy.validate(url, lambda _host, ips=ips: ips)
        with self.assertRaises(SsrfViolation):
            policy.validate("http://public.example/", lambda _host: ["8.8.8.8"])

    def test_blocks_mixed_dns_answer_to_reduce_rebinding_risk(self) -> None:
        policy = SsrfPolicy(allowed_hosts=frozenset({"api.example.test"}))
        with self.assertRaises(SsrfViolation):
            policy.validate("https://api.example.test/data", lambda _host: ["8.8.8.8", "127.0.0.1"])

    def test_returns_public_ips_for_connector_pinning(self) -> None:
        target = SsrfPolicy(allowed_hosts=frozenset({"api.example.test"})).validate(
            "https://api.example.test/data", lambda _host: ["8.8.8.8", "1.1.1.1"]
        )
        self.assertEqual(target.resolved_ips, ("8.8.8.8", "1.1.1.1"))


class RateLimitTests(unittest.TestCase):
    def test_token_bucket_blocks_and_recovers_deterministically(self) -> None:
        limiter = TokenBucketLimiter(capacity=2, refill_per_second=1.0)
        self.assertTrue(limiter.check("tenant:u:route", now=100).allowed)
        self.assertTrue(limiter.check("tenant:u:route", now=100).allowed)
        blocked = limiter.check("tenant:u:route", now=100)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.retry_after_seconds, 1)
        self.assertTrue(limiter.check("tenant:u:route", now=101).allowed)


class ServiceTrustTests(unittest.TestCase):
    def test_workload_scope_audience_and_freshness_are_enforced(self) -> None:
        policy = ServiceTrustPolicy(
            expected_audience="deskpilot-api",
            allowed_workloads={"worker/remediation": frozenset({"incident:read", "remediation:execute"})},
        )
        ok = ServicePrincipal("worker/remediation", "deskpilot-api", "tenant-a", frozenset({"remediation:execute"}), 100, 200)
        policy.authorize(ok, required_scope="remediation:execute", now=110)
        with self.assertRaises(ServiceIdentityError):
            policy.authorize(ServicePrincipal("evil", "deskpilot-api", None, frozenset({"remediation:execute"}), 100, 200), required_scope="remediation:execute", now=110)
        with self.assertRaises(ServiceIdentityError):
            policy.authorize(ServicePrincipal("worker/remediation", "wrong", None, frozenset({"remediation:execute"}), 100, 200), required_scope="remediation:execute", now=110)


class RequestAndSecretTests(unittest.TestCase):
    def test_request_limits_and_request_id(self) -> None:
        limits = RequestLimits(max_content_length=100)
        with self.assertRaises(RequestValidationError):
            limits.validate(method="POST", content_length=101, content_type="application/json")
        with self.assertRaises(RequestValidationError):
            limits.validate(method="PATCH", content_length=10, content_type="text/plain")
        self.assertEqual(validate_request_id("req-12345678"), "req-12345678")
        with self.assertRaises(RequestValidationError):
            validate_request_id("bad header\nattack")

    def test_inline_secrets_are_rejected_but_secret_refs_are_allowed(self) -> None:
        SecretRef("vault", "deskpilot/prod/database")
        with self.assertRaises(SecretConfigurationError):
            reject_inline_secrets({"database_password": "plaintext"})


if __name__ == "__main__":
    unittest.main()
