import { z } from "zod";

export const AuthSessionSchema = z.object({
  authenticated: z.literal(true),
  userId: z.string().min(1),
  tenantId: z.string().min(1),
  roles: z.array(z.string().min(1)),
  capabilities: z.array(z.string().min(1)),
  issuedAt: z.number().int().nonnegative(),
  expiresAt: z.number().int().positive(),
  authTime: z.number().int().nonnegative(),
  authVersion: z.number().int().positive(),
  permissionVersion: z.number().int().positive(),
  acr: z.string().nullable(),
  amr: z.array(z.string()),
});

export const AnonymousSessionSchema = z.object({ authenticated: z.literal(false) });
export const BrowserSessionSchema = z.discriminatedUnion("authenticated", [AuthSessionSchema, AnonymousSessionSchema]);
export type BrowserSession = z.infer<typeof BrowserSessionSchema>;

export const StepUpRequiredSchema = z.object({
  code: z.literal("step_up_required"),
  action: z.string().min(1),
  resourceId: z.string().min(1),
  authorizationUrl: z.string().url(),
});
export type StepUpRequired = z.infer<typeof StepUpRequiredSchema>;

export const LogoutResponseSchema = z.object({
  loggedOut: z.literal(true),
  logoutUrl: z.string().url().nullable().optional(),
});
export type LogoutResponse = z.infer<typeof LogoutResponseSchema>;
