import { z } from "zod";

export const UuidSchema = z.string().uuid();
export const IsoDateTimeSchema = z.string().datetime();

export const CorrelationIdSchema = z.string().min(8).max(128);

export const PaginationSchema = z.object({
  page: z.number().int().positive(),
  pageSize: z.number().int().min(1).max(200),
  total: z.number().int().nonnegative()
});
