import { z } from "zod";
import { IsoDateTimeSchema, UuidSchema } from "./common.schema";

export const IncidentStatusSchema = z.enum([
  "new",
  "triaging",
  "diagnosing",
  "awaiting_approval",
  "remediating",
  "monitoring",
  "resolved",
  "closed"
]);

export const IncidentSeveritySchema = z.enum(["low", "medium", "high", "critical"]);

export const IncidentSchema = z.object({
  id: UuidSchema,
  tenantId: UuidSchema,
  title: z.string().min(1).max(200),
  description: z.string().max(5000),
  status: IncidentStatusSchema,
  severity: IncidentSeveritySchema,
  createdAt: IsoDateTimeSchema,
  updatedAt: IsoDateTimeSchema
});

export type Incident = z.infer<typeof IncidentSchema>;
export type IncidentStatus = z.infer<typeof IncidentStatusSchema>;
