from __future__ import annotations

from http.cookies import SimpleCookie


SESSION_COOKIE = "__Host-deskpilot_session"
CSRF_COOKIE = "__Host-deskpilot_csrf"


def session_cookie_header(token: str, *, max_age: int) -> str:
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE] = token
    morsel = cookie[SESSION_COOKIE]
    morsel["path"] = "/"
    morsel["secure"] = True
    morsel["httponly"] = True
    morsel["samesite"] = "Lax"
    morsel["max-age"] = str(max_age)
    return morsel.OutputString()


def clear_session_cookie_header() -> str:
    return f"{SESSION_COOKIE}=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0"


def csrf_cookie_header(token: str, *, max_age: int) -> str:
    # Deliberately readable by same-origin JavaScript so it can be mirrored into X-CSRF-Token.
    return f"{CSRF_COOKIE}={token}; Path=/; Secure; SameSite=Strict; Max-Age={max_age}"
