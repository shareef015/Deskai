import { z } from "zod";

export const TraceContextSchema = z.object({
  traceId: z.string().regex(/^[a-f0-9]{32}$/),
  spanId: z.string().regex(/^[a-f0-9]{16}$/),
  traceparent: z.string().regex(/^00-[a-f0-9]{32}-[a-f0-9]{16}-(00|01)$/),
  correlationId: z.string().min(1).max(128),
  runId: z.string().min(1).max(128),
});

export const QualitySnapshotSchema = z.object({
  retrievalPrecision: z.number().min(0).max(1),
  retrievalRecall: z.number().min(0).max(1),
  groundedness: z.number().min(0).max(1),
  citationIntegrity: z.number().min(0).max(1),
  routeAccuracy: z.number().min(0).max(1),
  toolSuccess: z.number().min(0).max(1),
  hallucinationRate: z.number().min(0).max(1),
  promptInjectionBlockRate: z.number().min(0).max(1),
  closureAccuracy: z.number().min(0).max(1),
  p95LatencyMs: z.number().nonnegative(),
  averageCostUsd: z.number().nonnegative(),
  releasePassed: z.boolean(),
});

export type QualitySnapshot = z.infer<typeof QualitySnapshotSchema>;
