# OIDC and OAuth authentication

DeskPilot delegates human authentication to the customer's OIDC provider. The
browser uses authorization code flow with PKCE S256, state and nonce. Tokens are
held in a server-side session and never exposed to browser JavaScript. Cookies
are Secure, HttpOnly, SameSite=Lax, path-bound, rotated after authentication and
protected against CSRF.

The API accepts bearer access tokens only after verifying the signature against
trusted issuer keys, an allowlisted asymmetric algorithm, exact issuer,
audience, expiry, issued-at time, subject and the dedicated DeskPilot tenant
claim. The authenticated tenant claim becomes immutable request context; body,
query, model and tool values cannot override it.

Missing or invalid authentication returns 401. A valid identity without the
required scope returns 403. Neither response echoes tokens, claims or validation
internals. Service identities use client credentials with tenant-bound scopes,
prefer sender-constrained tokens and cannot impersonate human authority.
