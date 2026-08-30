from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_identity.audit import IdentityAuditLog
from deskpilot_identity.logout import BACKCHANNEL_LOGOUT_EVENT, BackChannelLogoutHandler, LogoutError, VerifiedLogoutToken
from deskpilot_identity.models import PermissionSnapshot, Principal, Role
from deskpilot_identity.oidc import OidcConfig, OidcError, OidcFlow, VerifiedIdToken
from deskpilot_identity.permission_drift import revoke_if_drifted
from deskpilot_identity.policy import AuthorizationPolicy, RequestContext, ResourceContext
from deskpilot_identity.sessions import SessionError, SessionManager
from deskpilot_identity.step_up import StepUpError, StepUpManager
from deskpilot_identity.enforcement import IdentityEnforcer
from deskpilot_identity.csrf import issue_csrf_token, validate_csrf_token
from deskpilot_identity.token_vault import InMemoryTokenVault, ProviderTokenSet, TokenVaultError


def principal(*, tenant: str = "tenant-a", subject: str = "user-1", permission_version: int = 1, oidc_sid: str | None = None) -> Principal:
    return Principal(
        user_id=subject,
        subject=subject,
        tenant_id=tenant,
        roles=frozenset({Role.SERVICE_DESK}),
        capabilities=frozenset({"incident:read", "diagnostic:run", "remediation:approve"}),
        auth_time=100,
        permission_version=permission_version,
        oidc_sid=oidc_sid,
    )


class SessionSecurityTests(unittest.TestCase):
    def test_rotation_prevents_session_fixation_reuse(self) -> None:
        manager = SessionManager(ttl_seconds=1000)
        token, old = manager.issue(principal(), now=100)
        new_token, new = manager.rotate(token, now=110, reason="login")
        self.assertNotEqual(old.session_id, new.session_id)
        with self.assertRaises(SessionError):
            manager.authenticate(token, now=111)
        self.assertEqual(manager.authenticate(new_token, now=111).session_id, new.session_id)

    def test_concurrent_session_limit_revokes_oldest(self) -> None:
        manager = SessionManager(ttl_seconds=1000, max_concurrent_sessions=2)
        t1, s1 = manager.issue(principal(), now=100)
        manager.issue(principal(), now=101)
        manager.issue(principal(), now=102)
        with self.assertRaises(SessionError):
            manager.authenticate(t1, now=103)
        self.assertEqual(len(manager.active_for_subject("user-1", "tenant-a", now=103)), 2)
        self.assertEqual(s1.revoke_reason, "concurrent_session_limit")

    def test_permission_drift_revokes_session(self) -> None:
        manager = SessionManager(ttl_seconds=1000)
        token, session = manager.issue(principal(), now=100)
        snapshot = PermissionSnapshot(
            subject="user-1", tenant_id="tenant-a", roles=frozenset({Role.VIEWER}),
            capabilities=frozenset({"incident:read"}), permission_version=2,
        )
        result = revoke_if_drifted(manager, session, snapshot, now=120)
        self.assertTrue(result.drifted)
        with self.assertRaises(SessionError):
            manager.authenticate(token, now=121)


class AuthorizationSecurityTests(unittest.TestCase):
    def test_cross_tenant_is_denied(self) -> None:
        policy = AuthorizationPolicy()
        decision = policy.evaluate(
            principal(), "incident:read",
            ResourceContext("tenant-b", "incident", "inc-1"), RequestContext(device_trust="managed"),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "cross_tenant_denied")

    def test_step_up_is_scoped_and_one_time(self) -> None:
        manager = SessionManager(ttl_seconds=1000)
        token, session = manager.issue(principal(), now=100)
        stepup = StepUpManager(ttl_seconds=300, allowed_acr_values=frozenset({"mfa"}))
        grant = stepup.issue(session, action="remediation:approve", resource_id="inc-1", verified_auth_time=120, acr="mfa", now=120)
        enforcer = IdentityEnforcer(manager, AuthorizationPolicy(), stepup)
        result = enforcer.authorize(
            token, action="remediation:approve",
            resource=ResourceContext("tenant-a", "incident", "inc-1"),
            request=RequestContext(device_trust="managed"), step_up_grant_id=grant.grant_id, now=121,
        )
        self.assertTrue(result.decision.allowed)
        replay = enforcer.authorize(
            token, action="remediation:approve",
            resource=ResourceContext("tenant-a", "incident", "inc-1"),
            request=RequestContext(device_trust="managed"), step_up_grant_id=grant.grant_id, now=122,
        )
        self.assertFalse(replay.decision.allowed)

    def test_step_up_rejects_unapproved_assurance(self) -> None:
        manager = SessionManager(ttl_seconds=1000)
        _, session = manager.issue(principal(), now=100)
        stepup = StepUpManager(ttl_seconds=300, allowed_acr_values=frozenset({"mfa"}))
        with self.assertRaises(StepUpError):
            stepup.issue(session, action="remediation:approve", resource_id="inc-1", verified_auth_time=120, acr="pwd", now=120)


class OidcSecurityTests(unittest.TestCase):
    def _config(self) -> OidcConfig:
        return OidcConfig(
            issuer="https://id.example.test", authorization_endpoint="https://id.example.test/authorize",
            token_endpoint="https://id.example.test/token", jwks_uri="https://id.example.test/jwks",
            client_id="deskpilot", redirect_uri="https://app.example.test/auth/callback",
        )

    def test_state_is_single_use_and_nonce_is_bound(self) -> None:
        flow = OidcFlow(self._config())
        _, tx = flow.begin(now=100)
        claims = VerifiedIdToken(
            issuer=self._config().issuer, audience=("deskpilot",), subject="user-1", nonce=tx.nonce,
            expires_at=500, issued_at=100, auth_time=100, tenant_id="tenant-a",
            roles=frozenset({Role.SERVICE_DESK}), capabilities=frozenset({"incident:read"}),
        )
        async def exchange(code: str, verifier: str):
            self.assertEqual(code, "code-1")
            self.assertEqual(verifier, tx.code_verifier)
            return {"id_token": "signed-token", "access_token": "server-only"}
        async def verify(raw: str):
            self.assertEqual(raw, "signed-token")
            return claims
        asyncio.run(flow.complete(code="code-1", state=tx.state, exchange=exchange, verify_id_token=verify, now=101))
        with self.assertRaises(OidcError):
            asyncio.run(flow.complete(code="code-1", state=tx.state, exchange=exchange, verify_id_token=verify, now=102))

    def test_nonce_mismatch_is_rejected(self) -> None:
        flow = OidcFlow(self._config())
        _, tx = flow.begin(now=100)
        claims = VerifiedIdToken(
            issuer=self._config().issuer, audience=("deskpilot",), subject="user-1", nonce="attacker-nonce",
            expires_at=500, issued_at=100, auth_time=100, tenant_id="tenant-a", roles=frozenset(), capabilities=frozenset(),
        )
        async def exchange(code: str, verifier: str): return {"id_token": "signed-token"}
        async def verify(raw: str): return claims
        with self.assertRaises(OidcError):
            asyncio.run(flow.complete(code="code", state=tx.state, exchange=exchange, verify_id_token=verify, now=101))


class LogoutSecurityTests(unittest.TestCase):
    def test_backchannel_logout_revokes_bound_session_and_blocks_replay(self) -> None:
        manager = SessionManager(ttl_seconds=1000)
        token, session = manager.issue(principal(oidc_sid="provider-session-7"), now=100)
        handler = BackChannelLogoutHandler(manager, issuer="https://id.example.test", client_id="deskpilot")
        logout = VerifiedLogoutToken(
            issuer="https://id.example.test", audience=("deskpilot",), subject=None, sid="provider-session-7",
            events={BACKCHANNEL_LOGOUT_EVENT: {}}, issued_at=110, jti="logout-1",
        )
        self.assertEqual(handler.apply(logout, now=111), 1)
        with self.assertRaises(SessionError): manager.authenticate(token, now=112)
        with self.assertRaises(LogoutError): handler.apply(logout, now=113)


class AuditTests(unittest.TestCase):
    def test_identity_audit_chain_is_verifiable(self) -> None:
        audit = IdentityAuditLog()
        audit.append("login.started", actor_subject="u", tenant_id="t", now=1)
        audit.append("login.completed", actor_subject="u", tenant_id="t", now=2)
        self.assertTrue(audit.verify_chain())


class TokenVaultSecurityTests(unittest.TestCase):
    def test_refresh_rotation_detects_reuse(self) -> None:
        vault = InMemoryTokenVault()
        vault.bind("s1", ProviderTokenSet("a1", 200, "r1", 1000))
        vault.rotate("s1", presented_refresh_token="r1", replacement=ProviderTokenSet("a2", 300, "r2", 1000))
        with self.assertRaises(TokenVaultError):
            vault.rotate("s1", presented_refresh_token="r1", replacement=ProviderTokenSet("a3", 400, "r3", 1000))
        self.assertIsNone(vault.get("s1"))


class CsrfBindingTests(unittest.TestCase):
    def test_csrf_token_is_bound_to_session_and_expiry(self) -> None:
        secret = b"test-secret-with-enough-entropy"
        token = issue_csrf_token("session-a", secret, now=100)
        self.assertTrue(validate_csrf_token(token, "session-a", secret, now=101))
        self.assertFalse(validate_csrf_token(token, "session-b", secret, now=101))
        self.assertFalse(validate_csrf_token(token, "session-a", secret, max_age_seconds=10, now=111))


if __name__ == "__main__":
    unittest.main()
