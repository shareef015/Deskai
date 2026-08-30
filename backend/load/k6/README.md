# Performance k6 Profiles

These scripts are deployment/staging load profiles. They intentionally do **not** embed credentials. Supply a synthetic load-test identity through environment variables and run only against an approved non-production environment.

Profiles:
- `api_incidents.js`: ramped request-arrival envelope and API latency/error thresholds.
- `sse_fanout.js`: sustained streaming connection pressure.
- `websocket_fanout.js`: WebSocket handshake/fan-out pressure.

The deterministic Python certificate is suitable for CI regression testing. k6 results are the source of truth for real capacity certification.
