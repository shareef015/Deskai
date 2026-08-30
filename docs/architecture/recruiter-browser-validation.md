# Recruiter demo browser validation

The recruiter journey is designed to execute in a real browser against the production Next.js build. It covers the successful conversation-to-resolution path, remote-access decline, unsuccessful employee verification, dashboard navigation, mobile drawer, keyboard focus order and deterministic reset.

Evidence includes desktop and mobile screenshots, visible-text assertions, console-error count, build fingerprint, synthetic seed and a hashed run manifest. The run is synthetic-only and performs no external endpoint or account side effects.

When the managed browser cannot route to the local preview, the attempt is recorded as blocked and no passing manifest or screenshots are created. A later run must still satisfy every evidence requirement; infrastructure failure never becomes fabricated evidence.
