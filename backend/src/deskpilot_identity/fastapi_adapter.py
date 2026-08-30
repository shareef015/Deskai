from __future__ import annotations

from collections.abc import Awaitable, Callable
import secrets
import time
from typing import Mapping
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .csrf import issue_csrf_token, validate_csrf_token
from .http_contract import CSRF_COOKIE, SESSION_COOKIE, clear_session_cookie_header, csrf_cookie_header, session_cookie_header
from .logout import BackChannelLogoutHandler, VerifiedLogoutToken, build_rp_logout_url
from .oidc import IdTokenVerifier, OidcFlow, TokenExchange
from .service import IdentityService
from .sessions import SessionError
from .token_vault import ProviderTokenSet


LogoutTokenVerifier = Callable[[str], Awaitable[VerifiedLogoutToken]]


def _provider_tokens(raw: Mapping[str, object], now: int) -> ProviderTokenSet | None:
    access = raw.get("access_token")
    if not isinstance(access, str) or not access:
        return None
    expires_in = raw.get("expires_in")
    access_expires = now + (int(expires_in) if isinstance(expires_in, (int, float)) else 300)
    refresh = raw.get("refresh_token")
    refresh_token = refresh if isinstance(refresh, str) and refresh else None
    refresh_expires_in = raw.get("refresh_expires_in")
    refresh_expires = now + int(refresh_expires_in) if isinstance(refresh_expires_in, (int, float)) else None
    raw_id = raw.get("id_token")
    id_token = raw_id if isinstance(raw_id, str) and raw_id else None
    return ProviderTokenSet(access, access_expires, refresh_token, refresh_expires, id_token=id_token)


def build_identity_router(
    *,
    service: IdentityService,
    oidc: OidcFlow,
    exchange: TokenExchange,
    verify_id_token: IdTokenVerifier,
    csrf_secret: bytes,
    end_session_endpoint: str | None = None,
    post_logout_redirect_uri: str | None = None,
    backchannel_handler: BackChannelLogoutHandler | None = None,
    verify_logout_token: LogoutTokenVerifier | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["identity"])

    @router.get("/login")
    async def login(return_path: str = "/") -> RedirectResponse:
        url, tx = oidc.begin(return_path=return_path)
        response = RedirectResponse(url, status_code=302)
        response.set_cookie("__Host-deskpilot_oidc_tx", tx.state, secure=True, httponly=True, samesite="lax", path="/")
        return response

    @router.get("/callback")
    async def callback(request: Request, code: str, state: str) -> RedirectResponse:
        tx_cookie = request.cookies.get("__Host-deskpilot_oidc_tx")
        if not tx_cookie or not secrets.compare_digest(tx_cookie, state):
            raise HTTPException(status_code=400, detail="oidc_transaction_binding_failed")
        now = int(time.time())
        principal, tx, raw_tokens = await oidc.complete(code=code, state=state, exchange=exchange, verify_id_token=verify_id_token, now=now)

        if tx.step_up_action is not None:
            current_token = request.cookies.get(SESSION_COOKIE)
            if not current_token:
                raise HTTPException(status_code=401, detail="step_up_session_missing")
            try:
                current = service.sessions.authenticate(current_token, now=now)
            except SessionError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            if tx.step_up_session_id != current.session_id or principal.subject != current.principal.subject or principal.tenant_id != current.principal.tenant_id:
                raise HTTPException(status_code=403, detail="step_up_identity_binding_failed")
            grant = service.step_up.issue(
                current, action=tx.step_up_action, resource_id=tx.step_up_resource_id or "",
                verified_auth_time=principal.auth_time, acr=principal.acr, now=now,
            )
            response = RedirectResponse(tx.return_path, status_code=302)
            response.set_cookie("__Host-deskpilot_stepup", grant.grant_id, secure=True, httponly=True, samesite="strict", path="/", max_age=service.step_up.ttl_seconds)
            response.set_cookie("__Host-deskpilot_oidc_tx", "", max_age=0, expires=0, path="/", secure=True, httponly=True, samesite="lax")
            return response

        session_token, session = service.complete_login(principal, _provider_tokens(raw_tokens, now), now=now)
        csrf = issue_csrf_token(session.session_id, csrf_secret, now=now)
        response = RedirectResponse(tx.return_path, status_code=302)
        response.headers.append("set-cookie", session_cookie_header(session_token, max_age=service.sessions.ttl_seconds))
        response.headers.append("set-cookie", csrf_cookie_header(csrf, max_age=min(service.sessions.ttl_seconds, 3600)))
        response.set_cookie("__Host-deskpilot_oidc_tx", "", max_age=0, expires=0, path="/", secure=True, httponly=True, samesite="lax")
        return response

    @router.get("/session")
    async def session_projection(request: Request) -> JSONResponse:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return JSONResponse({"authenticated": False})
        try:
            session = service.sessions.authenticate(token)
        except SessionError:
            return JSONResponse({"authenticated": False})
        p = session.principal
        response = JSONResponse({
            "authenticated": True, "userId": p.user_id, "tenantId": p.tenant_id,
            "roles": sorted(role.value for role in p.roles), "capabilities": sorted(p.capabilities),
            "issuedAt": session.issued_at, "expiresAt": session.expires_at, "authTime": p.auth_time,
            "authVersion": session.auth_version, "permissionVersion": session.permission_version,
            "acr": p.acr, "amr": list(p.amr),
        }, headers={"cache-control": "no-store"})
        fresh_csrf = issue_csrf_token(session.session_id, csrf_secret)
        response.headers.append("set-cookie", csrf_cookie_header(fresh_csrf, max_age=min(service.sessions.ttl_seconds, 3600)))
        return response

    @router.post("/step-up")
    async def begin_step_up(request: Request) -> JSONResponse:
        token = request.cookies.get(SESSION_COOKIE)
        csrf_cookie = request.cookies.get(CSRF_COOKIE)
        csrf_header = request.headers.get("x-csrf-token")
        if not token:
            raise HTTPException(status_code=401, detail="session_missing")
        try:
            session = service.sessions.authenticate(token)
        except SessionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header) or not validate_csrf_token(csrf_cookie, session.session_id, csrf_secret):
            raise HTTPException(status_code=403, detail="csrf_failed")
        body = await request.json()
        action, resource_id = body.get("action"), body.get("resourceId")
        if not isinstance(action, str) or not action or not isinstance(resource_id, str) or not resource_id:
            raise HTTPException(status_code=422, detail="invalid_step_up_scope")
        url, tx = oidc.begin(
            return_path=request.headers.get("referer", "/"), step_up_action=action, step_up_resource_id=resource_id,
            step_up_session_id=session.session_id, force_reauth=True,
        )
        response = JSONResponse({"code": "step_up_required", "action": action, "resourceId": resource_id, "authorizationUrl": url})
        response.set_cookie("__Host-deskpilot_oidc_tx", tx.state, secure=True, httponly=True, samesite="lax", path="/")
        return response

    @router.post("/logout")
    async def logout(request: Request) -> JSONResponse:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            response = JSONResponse({"loggedOut": True})
            response.headers.append("set-cookie", clear_session_cookie_header())
            response.set_cookie(CSRF_COOKIE, "", max_age=0, expires=0, path="/", secure=True, httponly=False, samesite="strict")
            response.set_cookie("__Host-deskpilot_stepup", "", max_age=0, expires=0, path="/", secure=True, httponly=True, samesite="strict")
            return response
        try:
            session = service.sessions.authenticate(token)
        except SessionError:
            response = JSONResponse({"loggedOut": True})
            response.headers.append("set-cookie", clear_session_cookie_header())
            response.set_cookie(CSRF_COOKIE, "", max_age=0, expires=0, path="/", secure=True, httponly=False, samesite="strict")
            response.set_cookie("__Host-deskpilot_stepup", "", max_age=0, expires=0, path="/", secure=True, httponly=True, samesite="strict")
            return response
        csrf_cookie = request.cookies.get(CSRF_COOKIE)
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header) or not validate_csrf_token(csrf_cookie, session.session_id, csrf_secret):
            raise HTTPException(status_code=403, detail="csrf_failed")
        body = await request.json()
        tokens = service.token_vault.get(session.session_id)
        if body.get("allSessions") is True:
            service.logout_all(session, now=int(time.time()))
        else:
            service.logout_session(session, now=int(time.time()))
        logout_url = None
        if end_session_endpoint:
            logout_url = build_rp_logout_url(
                end_session_endpoint=end_session_endpoint, id_token_hint=tokens.id_token if tokens else None,
                post_logout_redirect_uri=post_logout_redirect_uri, state=secrets.token_urlsafe(24),
            )
        response = JSONResponse({"loggedOut": True, "logoutUrl": logout_url})
        response.headers.append("set-cookie", clear_session_cookie_header())
        response.set_cookie(CSRF_COOKIE, "", max_age=0, expires=0, path="/", secure=True, httponly=False, samesite="strict")
        response.set_cookie("__Host-deskpilot_stepup", "", max_age=0, expires=0, path="/", secure=True, httponly=True, samesite="strict")
        return response

    @router.post("/backchannel-logout")
    async def backchannel_logout(request: Request) -> JSONResponse:
        if backchannel_handler is None or verify_logout_token is None:
            raise HTTPException(status_code=501, detail="backchannel_logout_not_configured")
        form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
        values = form.get("logout_token", [])
        raw = values[0] if values else None
        if not isinstance(raw, str) or not raw:
            raise HTTPException(status_code=400, detail="logout_token_missing")
        verified = await verify_logout_token(raw)
        backchannel_handler.apply(verified, now=int(time.time()))
        return JSONResponse({"ok": True})

    return router
