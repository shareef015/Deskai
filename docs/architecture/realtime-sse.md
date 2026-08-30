# Real-time incident activity streaming

The employee and engineer interfaces consume authenticated Server-Sent Events
for a single authorized incident. Tenant scope comes from the verified identity,
not the URL. Authorization is checked before opening the stream, and the stream
uses short tenant-bound database reads instead of holding one long transaction.

Event IDs are incident aggregate sequence numbers. A reconnect sends
`Last-Event-ID`; replay begins exclusively after it in batches of at most 100.
Delivery can repeat across network failures, so clients deduplicate by event ID.

The server emits a comment heartbeat every 15 seconds, disables proxy buffering,
holds no unbounded application queue and awaits transport backpressure. Streams
close after 30 minutes so authentication and authorization are periodically
re-evaluated. Clients reconnect with bounded jitter.
