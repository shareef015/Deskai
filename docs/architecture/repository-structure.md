# Repository Structure

DeskPilot is a modular monorepo with independently deployable services and explicit shared contracts.

| Path | Ownership |
|---|---|
| `apps/web` | Employee and technician web experience |
| `services/api` | Public application API and authentication boundary |
| `services/ai-service` | LangGraph orchestration and policy decisions |
| `services/rag-service` | Governed retrieval, ranking and citations |
| `services/mcp-gateway` | Consent-bound Windows tool execution |
| `services/worker` | Durable asynchronous jobs |
| `packages` | Versioned Python and TypeScript contracts |
| `contracts` | Auditable product and protocol specifications |
| `infra` | Private deployment definitions |
| `config` | Non-secret environment configuration templates |
| `data/synthetic` | Safe demonstration and evaluation fixtures |

Deployables communicate through versioned APIs or events. They never import another deployable's implementation. The MCP gateway is the only server-side component permitted to request endpoint execution.
