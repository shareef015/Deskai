import type { Incident } from "../schemas";

export type UiError =
  | { kind: "authentication"; message: string }
  | { kind: "authorization"; message: string }
  | { kind: "validation"; message: string }
  | { kind: "network"; message: string }
  | { kind: "timeout"; message: string }
  | { kind: "contract"; message: string; correlationId?: string }
  | { kind: "rate_limit"; message: string }
  | { kind: "not_found"; message: string }
  | { kind: "conflict"; message: string }
  | { kind: "server"; message: string }
  | { kind: "agent_execution"; message: string }
  | { kind: "tool_execution"; message: string };

export type IncidentViewState =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "success"; incident: Incident }
  | { state: "empty" }
  | { state: "error"; error: UiError };

export type AgentExecutionState =
  | { state: "queued" }
  | { state: "running"; step: string }
  | { state: "awaiting-human"; approvalId: string }
  | { state: "completed"; resultSummary: string }
  | { state: "failed"; error: UiError }
  | { state: "cancelled" };

export function assertNever(value: never): never {
  throw new Error(`Unexpected state: ${String(value)}`);
}
