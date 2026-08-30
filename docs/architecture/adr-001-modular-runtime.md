# ADR: Modular Runtime Boundaries

Status: accepted.

Use web, API, AI, RAG, MCP gateway and worker boundaries. This keeps endpoint
authority separate from probabilistic reasoning without creating unnecessary
microservices. Every stateless boundary can later scale independently.
