from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from deskpilot_api_security.fastapi_app import ApiDependencies, build_secure_api
from deskpilot_api_security.repository import TenantRecord, TenantScopedRepository
from deskpilot_api_security.tenant import TenantContext
from deskpilot_identity.csrf import issue_csrf_token
from deskpilot_identity.http_contract import CSRF_COOKIE, SESSION_COOKIE
from deskpilot_identity.models import Principal, Role
from deskpilot_identity.sessions import SessionManager


def principal(tenant: str, subject: str = "user-1") -> Principal:
    return Principal(
        user_id=subject,
        tenant_id=tenant,
        subject=subject,
        roles=frozenset({Role.SERVICE_DESK}),
        capabilities=frozenset({"incident:read", "incident:update"}),
        auth_time=1,
    )


CSRF_SECRET = b"database-test-csrf-secret-32bytes"


class SecureApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sessions = SessionManager(ttl_seconds=3600)
        self.repo = TenantScopedRepository([
            TenantRecord("inc-a", "tenant-a", {"title": "Printer A", "status": "new"}),
            TenantRecord("inc-b", "tenant-b", {"title": "Printer B", "status": "new"}),
        ])
        self.client = TestClient(build_secure_api(ApiDependencies(self.sessions, self.repo, CSRF_SECRET)), base_url="https://testserver")

    def login_cookie(self, tenant: str = "tenant-a") -> tuple[str, str]:
        token, session = self.sessions.issue(principal(tenant))
        csrf = issue_csrf_token(session.session_id, CSRF_SECRET)
        self.client.cookies.set(SESSION_COOKIE, token)
        self.client.cookies.set(CSRF_COOKIE, csrf)
        return token, csrf

    def test_protected_endpoint_requires_authentication(self) -> None:
        response = self.client.get("/api/incidents/inc-a")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "unauthenticated")
        self.assertNotIn("traceback", response.text.lower())

    def test_bola_cross_tenant_identifier_is_not_found(self) -> None:
        self.login_cookie("tenant-a")
        response = self.client.get("/api/incidents/inc-b")
        self.assertEqual(response.status_code, 404)

    def test_same_tenant_object_can_be_read_and_updated(self) -> None:
        _, csrf = self.login_cookie("tenant-a")
        get = self.client.get("/api/incidents/inc-a")
        self.assertEqual(get.status_code, 200)
        patch = self.client.patch("/api/incidents/inc-a", json={"status": "resolved"}, headers={"x-csrf-token": csrf})
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["status"], "resolved")
        self.assertEqual(patch.json()["tenantId"], "tenant-a")

    def test_mass_assignment_extra_property_is_rejected(self) -> None:
        _, csrf = self.login_cookie("tenant-a")
        response = self.client.patch("/api/incidents/inc-a", json={"status": "resolved", "tenant_id": "tenant-b"}, headers={"x-csrf-token": csrf})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.repo.get(TenantContext("tenant-a", "u"), "inc-a").tenant_id, "tenant-a")

    def test_oversized_request_is_rejected_before_handler(self) -> None:
        _, csrf = self.login_cookie("tenant-a")
        response = self.client.patch(
            "/api/incidents/inc-a",
            content=b"x" * 1_048_577,
            headers={"content-type": "application/json", "x-csrf-token": csrf},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_request")

    def test_state_changing_request_requires_session_bound_csrf(self) -> None:
        self.login_cookie("tenant-a")
        response = self.client.patch("/api/incidents/inc-a", json={"status": "resolved"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "csrf_rejected")

    def test_invalid_host_is_rejected(self) -> None:
        token, _ = self.sessions.issue(principal("tenant-a"))
        hostile = TestClient(build_secure_api(ApiDependencies(self.sessions, self.repo, CSRF_SECRET)), base_url="https://evil.example")
        hostile.cookies.set(SESSION_COOKIE, token)
        response = hostile.get("/api/incidents/inc-a")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
