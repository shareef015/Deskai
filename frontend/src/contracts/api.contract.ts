import { z } from "zod";

export class ContractViolationError extends Error {
  constructor(
    public readonly contract: string,
    public readonly issues: readonly z.core.$ZodIssue[]
  ) {
    super(`Contract validation failed: ${contract}`);
    this.name = "ContractViolationError";
  }
}

export async function parseJsonContract<T>(
  response: Response,
  schema: z.ZodType<T>,
  contract: string
): Promise<T> {
  const raw: unknown = await response.json();
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    throw new ContractViolationError(contract, parsed.error.issues);
  }
  return parsed.data;
}
