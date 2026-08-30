# Distributed rate limiting and API protection

Authenticated requests consume tenant, user and network token buckets in one
atomic Redis script. The script uses Redis server time, calculates every bucket
before writing, and decrements none when any dimension lacks capacity. This
prevents partial consumption and works consistently across API replicas.

Tenant identity comes from the verified claim. User subjects and network
addresses are keyed-HMAC pseudonyms in Redis and never appear raw in keys or
logs. Forwarded addresses are accepted only from configured trusted proxies.
Expensive lifecycle, diagnostic and remediation operations consume more tokens.

Allowed responses expose standard limit, remaining and reset information.
Rejections return 429 with `Retry-After` and no-store caching. Redis failure
fails authenticated mutations and authentication endpoints closed with 503;
health checks bypass limiting. There is no silent per-process fallback.
