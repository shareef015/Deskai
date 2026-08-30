# Production Production Evidence Schema

Every blocking control requires a real production evidence record.

Required fields:

- `control_id`
- `status`: `pass`, `fail`, or `not_run`
- `source`: immutable evidence path/reference; `synthetic` is rejected
- `observed_at`: timestamp from the real production window
- `fingerprint`: SHA-256 or equivalent immutable evidence fingerprint
- `environment`: must be `production`
- `approver`: required for human-approval controls
- `notes`: optional non-secret context

Production evidence must not contain tokens, credentials, private keys, raw sensitive prompts, or secret values.
