export interface ReconnectPolicy {
  readonly maxAttempts: number;
  readonly baseDelayMs: number;
  readonly maxDelayMs: number;
}

export const DEFAULT_STREAM_RECONNECT_POLICY: ReconnectPolicy = {
  maxAttempts: 12,
  baseDelayMs: 500,
  maxDelayMs: 15_000,
};

export function reconnectDelay(attempt: number, policy = DEFAULT_STREAM_RECONNECT_POLICY): number | null {
  if (attempt < 1 || attempt > policy.maxAttempts) return null;
  return Math.min(policy.maxDelayMs, policy.baseDelayMs * 2 ** Math.min(attempt - 1, 8));
}
