import { z } from "zod";
import { IsoDateTimeSchema, UuidSchema } from "./common.schema";

export const ApprovalStatusSchema = z.enum(["pending", "approved", "rejected", "expired"]);

export const ApprovalRequestSchema = z.object({
  id: UuidSchema,
  incidentId: UuidSchema,
  action: z.string().min(1),
  target: z.string().min(1),
  reason: z.string().min(1),
  risk: z.enum(["low", "medium", "high"]),
  rollbackAvailable: z.boolean(),
  status: ApprovalStatusSchema,
  expiresAt: IsoDateTimeSchema
});

export type ApprovalRequest = z.infer<typeof ApprovalRequestSchema>;
