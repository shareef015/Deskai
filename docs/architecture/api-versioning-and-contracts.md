# API versioning and contract governance

The public API uses a URI major version (`/api/v1`). Backward-compatible additions remain in the same major version; removals, newly required request fields, narrowed enums, and removed responses require a new major API and an explicit migration window.

FastAPI generates the runtime schema deterministically and attaches a SHA-256 schema digest. The reviewed JSON contract is the source for Python schemas and the TypeScript client. CI validates unique operation IDs, the public server prefix, self-compatibility, and policy alignment. A release candidate must compare its generated schema with the last promoted contract; detected breaking changes block release.

Authentication and problem responses are documented. Tenant identity is derived from the authenticated principal and is never accepted as a caller-selected header or query parameter.
