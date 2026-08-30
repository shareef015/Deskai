import { z } from "zod";

export const DemoPersonaSchema = z.object({
  personaId: z.string().min(1),
  displayName: z.string().min(1),
  role: z.enum(["recruiter", "service_desk_engineer", "approver", "reviewer"]),
  tenantId: z.string().min(1),
  synthetic: z.literal(true),
});

export const DemoScenarioSchema = z.object({
  scenarioId: z.string().min(1),
  label: z.string().min(1),
  domain: z.enum(["printer", "outlook"]),
  expected: z.enum(["closed", "diagnosing", "denied"]),
});

export const DemoRunStateSchema = z.enum([
  "ready",
  "greeting",
  "intake",
  "retrieval",
  "diagnosis",
  "approval",
  "remediation",
  "verification",
  "closed",
  "diagnosing",
  "denied",
]);

export type DemoPersona = z.infer<typeof DemoPersonaSchema>;
export type DemoScenario = z.infer<typeof DemoScenarioSchema>;
export type DemoRunState = z.infer<typeof DemoRunStateSchema>;
