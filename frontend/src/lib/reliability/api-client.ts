import { z } from "zod";
import { DEFAULT_RETRY_POLICY, backoffDelayMs, sleep, type RetryPolicy } from "./retry";

export class ApiTimeoutError extends Error {
  constructor(readonly timeoutMs: number) {
    super(`API request exceeded ${timeoutMs}ms`);
    this.name = "ApiTimeoutError";
  }
}

export class ApiHttpError extends Error {
  constructor(readonly status: number, readonly requestId?: string) {
    super(`API request failed with HTTP ${status}`);
    this.name = "ApiHttpError";
  }
}

export interface ApiRequestOptions<T> {
  readonly schema: z.ZodType<T>;
  readonly signal?: AbortSignal;
  readonly timeoutMs?: number;
  readonly retryPolicy?: RetryPolicy;
  readonly idempotencyKey?: string;
  readonly requestKey?: string;
}

function isMethodRetrySafe(method: string, idempotencyKey?: string): boolean {
  return ["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase()) || Boolean(idempotencyKey);
}

export async function apiRequest<T>(
  input: RequestInfo | URL,
  init: RequestInit,
  options: ApiRequestOptions<T>,
): Promise<T> {
  const timeoutMs = options.timeoutMs ?? 15_000;
  const policy = options.retryPolicy ?? DEFAULT_RETRY_POLICY;
  const method = init.method ?? "GET";
  let lastError: unknown;

  for (let attempt = 1; attempt <= policy.maxAttempts; attempt += 1) {
    const timeoutController = new AbortController();
    const timeout = globalThis.setTimeout(
      () => timeoutController.abort(new ApiTimeoutError(timeoutMs)),
      timeoutMs,
    );
    const signal = options.signal
      ? AbortSignal.any([options.signal, timeoutController.signal])
      : timeoutController.signal;

    try {
      const headers = new Headers(init.headers);
      if (options.idempotencyKey) headers.set("Idempotency-Key", options.idempotencyKey);
      headers.set("Accept", "application/json");

      const response = await fetch(input, { ...init, headers, signal });
      if (!response.ok) {
        const error = new ApiHttpError(response.status, response.headers.get("x-request-id") ?? undefined);
        const mayRetry = isMethodRetrySafe(method, options.idempotencyKey)
          && policy.retryableStatusCodes.has(response.status)
          && attempt < policy.maxAttempts;
        if (!mayRetry) throw error;
        lastError = error;
      } else {
        const raw: unknown = await response.json();
        return options.schema.parse(raw);
      }
    } catch (error: unknown) {
      if (options.signal?.aborted) throw options.signal.reason ?? error;
      const retryableNetworkFailure = !(error instanceof z.ZodError)
        && !(error instanceof ApiHttpError && !policy.retryableStatusCodes.has(error.status))
        && isMethodRetrySafe(method, options.idempotencyKey)
        && attempt < policy.maxAttempts;
      if (!retryableNetworkFailure) throw error;
      lastError = error;
    } finally {
      globalThis.clearTimeout(timeout);
    }

    await sleep(backoffDelayMs(attempt, policy), options.signal);
  }

  throw lastError instanceof Error ? lastError : new Error("API request failed after retries");
}
