import { z } from "zod";
import { CorrelationIdSchema } from "./common.schema";

export const ApiErrorSchema = z.object({
  code: z.string().min(1),
  message: z.string().min(1),
  correlationId: CorrelationIdSchema.optional(),
  details: z.record(z.string(), z.unknown()).optional()
});

export type ApiErrorPayload = z.infer<typeof ApiErrorSchema>;
