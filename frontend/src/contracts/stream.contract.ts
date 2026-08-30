import { z } from "zod";

export const AgentStreamEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("analysis_started"), runId: z.string().min(1) }),
  z.object({ type: z.literal("evidence_retrieved"), runId: z.string().min(1), count: z.number().int().nonnegative() }),
  z.object({ type: z.literal("approval_required"), runId: z.string().min(1), approvalId: z.string().min(1) }),
  z.object({ type: z.literal("remediation_started"), runId: z.string().min(1) }),
  z.object({ type: z.literal("remediation_succeeded"), runId: z.string().min(1) }),
  z.object({ type: z.literal("failed"), runId: z.string().min(1), message: z.string().min(1) })
]);

export type AgentStreamEvent = z.infer<typeof AgentStreamEventSchema>;

export function parseAgentStreamEvent(payload: unknown): AgentStreamEvent {
  return AgentStreamEventSchema.parse(payload);
}
