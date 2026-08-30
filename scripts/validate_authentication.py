from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/authentication-policy.json").read_text())
    verifier = (ROOT / "services/api/src/deskpilot_api/auth/verifier.py").read_text()
    dependency = (ROOT / "services/api/src/deskpilot_api/auth/dependencies.py").read_text()
    flow = policy.get("interactive_flow", {})
    if flow.get("grant") != "authorization_code" or flow.get("pkce") != "S256":
        errors.append("interactive login must use authorization code with PKCE S256")
    if flow.get("implicit_grant_allowed") is not False or flow.get("password_grant_allowed") is not False:
        errors.append("legacy OAuth grants must be prohibited")
    for token in ('{"RS256", "ES256"}', '"require": ["exp", "iat", "iss", "aud", "sub"]', "UUID(str(claims[self._tenant_claim]))"):
        if token not in verifier:
            errors.append(f"token validation control missing: {token}")
    if "request.state.tenant_id = principal.tenant_id" not in dependency:
        errors.append("verified tenant claim is not bound to request context")
    session = policy.get("browser_session", {})
    for key in ("cookie_http_only", "cookie_secure", "server_side_session", "csrf_protection_required"):
        if session.get(key) is not True:
            errors.append(f"browser session control missing: {key}")
    if session.get("tokens_exposed_to_browser_javascript") is not False:
        errors.append("browser JavaScript must not receive tokens")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("OIDC authentication validation passed")
