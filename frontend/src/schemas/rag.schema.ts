import { z } from "zod";

export const CitationSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  source: z.string().min(1),
  excerpt: z.string().max(2000),
  confidence: z.number().min(0).max(1)
});

export const RagAnswerSchema = z.object({
  answer: z.string(),
  grounded: z.boolean(),
  citations: z.array(CitationSchema),
  confidence: z.number().min(0).max(1)
});

export type RagAnswer = z.infer<typeof RagAnswerSchema>;
