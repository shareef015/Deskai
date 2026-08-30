import { z } from "zod";

const RecoveryEnvelopeSchema = z.object({
  version: z.literal(1),
  savedAt: z.number().int().nonnegative(),
  tenantId: z.string().min(1),
  route: z.string().min(1),
  incidentId: z.string().optional(),
  selectedPanel: z.string().optional(),
  lastEventId: z.string().optional(),
});

export type RecoveryEnvelope = z.infer<typeof RecoveryEnvelopeSchema>;

export interface RecoveryStore {
  save(state: RecoveryEnvelope): void;
  load(tenantId: string, maxAgeMs?: number): RecoveryEnvelope | null;
  clear(): void;
}

export function createBrowserRecoveryStore(storage: Storage, key = "deskpilot:recovery:v1"): RecoveryStore {
  return {
    save(state): void {
      RecoveryEnvelopeSchema.parse(state);
      storage.setItem(key, JSON.stringify(state));
    },
    load(tenantId, maxAgeMs = 8 * 60 * 60 * 1000): RecoveryEnvelope | null {
      const raw = storage.getItem(key);
      if (!raw) return null;
      try {
        const parsed = RecoveryEnvelopeSchema.safeParse(JSON.parse(raw) as unknown);
        if (!parsed.success || parsed.data.tenantId !== tenantId || Date.now() - parsed.data.savedAt > maxAgeMs) {
          storage.removeItem(key);
          return null;
        }
        return parsed.data;
      } catch {
        storage.removeItem(key);
        return null;
      }
    },
    clear(): void {
      storage.removeItem(key);
    },
  };
}
