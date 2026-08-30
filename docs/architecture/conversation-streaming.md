# Conversation Streaming

The employee conversation channel uses typed durable message and assistant-delta events. Sends are tenant- and employee-bound, cursor-checked and idempotent. Reconnect requests continue after the last committed cursor while duplicate history is discarded.

Messages, deltas and rendered history are bounded. Obvious secret assignments are redacted at ingress, attachments remain disabled, and the interface reminds employees not to provide passwords. Employee stop takes priority over generation and prevents further conversation or diagnostic progression.

The accessible live region announces streamed responses without moving keyboard focus. Consent language describes narrow read-only scope and never implies that conversation alone authorizes diagnostics or remediation.
