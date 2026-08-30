from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from deskpilot_identity.audit import IdentityAuditLog
from deskpilot_identity.enforcement import IdentityEnforcer
from deskpilot_identity.fastapi_adapter import build_identity_router
from deskpilot_identity.models import Role
from deskpilot_identity.oidc import OidcConfig, OidcFlow, VerifiedIdToken
from deskpilot_identity.policy import AuthorizationPolicy
from deskpilot_identity.service import IdentityService
from deskpilot_identity.sessions import SessionManager
from deskpilot_identity.step_up import StepUpManager


class FastApiIdentityFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = IdentityAuditLog()
        self.sessions = SessionManager(audit=self.audit, ttl_seconds=3600, max_concurrent_sessions=2)
        self.step_up = StepUpManager(ttl_seconds=300, allowed_acr_values=frozenset({"mfa"}))
        self.enforcer = IdentityEnforcer(self.sessions, AuthorizationPolicy(), self.step_up)
        self.service = IdentityService(
            sessions=self.sessions, enforcer=self.enforcer, step_up=self.step_up, audit=self.audit
        )
        self.flow = OidcFlow(
            OidcConfig(
                issuer="https://id.example.test",
                authorization_endpoint="https://id.example.test/authorize",
                token_endpoint="https://id.example.test/token",
                jwks_uri="https://id.example.test/jwks",
                client_id="deskpilot",
                redirect_uri="https://testserver/api/auth/callback",
                acr_values=("mfa",),
            )
        )
        self.nonce_by_code: dict[str, str] = {}

        async def exchange(code: str, verifier: str):
            self.assertGreater(len(verifier), 40)
            return {
                "id_token": f"id:{code}",
                "access_token": f"access:{code}",
                "refresh_token": f"refresh:{code}",
                "expires_in": 300,
            }

        async def verify_id_token(raw: str):
            code = raw.removeprefix("id:")
            now = int(time.time())
            return VerifiedIdToken(
                issuer="https://id.example.test",
                audience=("deskpilot",),
                subject="user-1",
                nonce=self.nonce_by_code[code],
                expires_at=now + 600,
                issued_at=now - 5,
                auth_time=now - 5,
                tenant_id="tenant-a",
                roles=frozenset({Role.APPROVER}),
                capabilities=frozenset({"incident:read", "remediation:approve"}),
                acr="mfa",
                amr=("pwd", "otp"),
                oidc_sid="provider-session-1",
            )

        app = FastAPI()
        app.include_router(
            build_identity_router(
                service=self.service,
                oidc=self.flow,
                exchange=exchange,
                verify_id_token=verify_id_token,
                csrf_secret=b"integration-test-secret-value",
                end_session_endpoint="https://id.example.test/logout",
                post_logout_redirect_uri="https://testserver/",
            )
        )
        self.client = TestClient(app, base_url="https://testserver")

    def _begin_and_callback(self, code: str, *, step_up: bool = False) -> None:
        if not step_up:
            login = self.client.get("/api/auth/login?return_path=/incidents/demo-incident", follow_redirects=False)
            self.assertEqual(login.status_code, 302)
            state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        else:
            csrf = self.client.cookies.get("__Host-deskpilot_csrf")
            self.assertIsNotNone(csrf)
            response = self.client.post(
                "/api/auth/step-up",
                json={"action": "remediation:approve", "resourceId": "incident-1"},
                headers={"X-CSRF-Token": csrf or ""},
            )
            self.assertEqual(response.status_code, 200)
            state = parse_qs(urlparse(response.json()["authorizationUrl"]).query)["state"][0]

        tx = self.flow.transactions._items[state]  # deterministic test inspection only
        self.nonce_by_code[code] = tx.nonce
        callback = self.client.get(
            "/api/auth/callback", params={"code": code, "state": state}, follow_redirects=False
        )
        self.assertEqual(callback.status_code, 302)

    def test_login_step_up_and_logout_end_to_end(self) -> None:
        self.assertEqual(self.client.get("/api/auth/session").json(), {"authenticated": False})

        self._begin_and_callback("login-code")
        session = self.client.get("/api/auth/session")
        self.assertEqual(session.status_code, 200)
        body = session.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["tenantId"], "tenant-a")
        self.assertNotIn("access_token", body)
        self.assertNotIn("refresh_token", body)

        self._begin_and_callback("stepup-code", step_up=True)
        self.assertIsNotNone(self.client.cookies.get("__Host-deskpilot_stepup"))

        csrf = self.client.cookies.get("__Host-deskpilot_csrf")
        logout = self.client.post(
            "/api/auth/logout",
            json={"allSessions": True},
            headers={"X-CSRF-Token": csrf or ""},
        )
        self.assertEqual(logout.status_code, 200)
        self.assertTrue(logout.json()["loggedOut"])
        self.assertTrue(logout.json()["logoutUrl"].startswith("https://id.example.test/logout?"))
        self.assertEqual(self.client.get("/api/auth/session").json(), {"authenticated": False})


if __name__ == "__main__":
    unittest.main()
