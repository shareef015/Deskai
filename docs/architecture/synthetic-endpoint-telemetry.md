# Synthetic endpoint telemetry and typed results

The telemetry generator creates one correlated evidence pack for every generated incident. Each pack contains a deterministic Windows health heartbeat and five typed, read-only capability results appropriate to Outlook, printing, scanning, or Windows networking.

Results have stable identifiers, bounded UTC timestamps and durations, correlation and incident lineage, compact typed output, mandatory redaction metadata, structured safe errors, and replay provenance. The corpus includes success, partial, failure, and timeout behavior without stack traces.

No result contains a shell command, unrestricted PowerShell, mailbox or document content, credentials, tokens, private keys, or personal data. Generation is offline and has no endpoint side effects.
