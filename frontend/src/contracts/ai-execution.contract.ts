import { z } from "zod";

export const AiExecutionStateSchema = z.enum([
  "intake",
  "retrieving",
  "grounding",
  "routing",
  "diagnosing",
  "awaiting_approval",
  "remediating",
  "verifying",
  "closed",
  "failed"
]);

export const GroundedCitationSchema = z.object({
  documentId: z.string().min(1),
  chunkId: z.string().min(1),
  tenantId: z.string().min(1),
  contentHash: z.string().regex(/^[a-f0-9]{64}$/)
});

export const AiExecutionEventSchema = z.object({
  sequence: z.number().int().positive(),
  state: AiExecutionStateSchema,
  eventType: z.string().min(1),
  tenantId: z.string().min(1),
  runId: z.string().min(1),
  details: z.record(z.string(), z.unknown()).default({})
});

export const AiExecutionSnapshotSchema = z.object({
  runId: z.string().min(1),
  tenantId: z.string().min(1),
  incidentId: z.string().min(1),
  state: AiExecutionStateSchema,
  citations: z.array(GroundedCitationSchema),
  events: z.array(AiExecutionEventSchema)
}).superRefine((snapshot, ctx) => {
  for (let index = 0; index < snapshot.events.length; index += 1) {
    const event = snapshot.events[index];
    if (event.sequence !== index + 1) {
      ctx.addIssue({ code: "custom", message: "execution_event_sequence_invalid", path: ["events", index, "sequence"] });
    }
    if (event.runId !== snapshot.runId || event.tenantId !== snapshot.tenantId) {
      ctx.addIssue({ code: "custom", message: "execution_event_context_mismatch", path: ["events", index] });
    }
  }
  for (const [index, citation] of snapshot.citations.entries()) {
    if (citation.tenantId !== snapshot.tenantId) {
      ctx.addIssue({ code: "custom", message: "citation_tenant_mismatch", path: ["citations", index, "tenantId"] });
    }
  }
});

export type AiExecutionEvent = z.infer<typeof AiExecutionEventSchema>;
export type AiExecutionSnapshot = z.infer<typeof AiExecutionSnapshotSchema>;
