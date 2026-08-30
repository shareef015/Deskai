const DEFAULT_SENSITIVE_KEYS = new Set([
  "authorization", "access_token", "refresh_token", "id_token", "token", "password",
  "secret", "cookie", "set-cookie", "api_key", "apikey", "session", "sessionid",
]);

function isSensitiveKey(key: string): boolean {
  const normalized = key.toLowerCase().replaceAll("-", "_");
  return DEFAULT_SENSITIVE_KEYS.has(normalized) || normalized.endsWith("_token") || normalized.endsWith("_secret");
}

export function redactSensitive<T>(input: T): T {
  return redactValue(input, new WeakSet<object>()) as T;
}

function redactValue(input: unknown, seen: WeakSet<object>): unknown {
  if (input === null || typeof input !== "object") return input;
  if (seen.has(input)) return "[Circular]";
  seen.add(input);
  if (Array.isArray(input)) return input.map((value) => redactValue(value, seen));
  const output: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(input)) {
    output[key] = isSensitiveKey(key) ? "[REDACTED]" : redactValue(value, seen);
  }
  return output;
}

export function scrubText(input: string): string {
  return input
    .replace(/Bearer\s+[A-Za-z0-9._~+\/-]+=*/gi, "Bearer [REDACTED]")
    .replace(/(access_token|refresh_token|id_token|api[_-]?key)=([^&\s]+)/gi, "$1=[REDACTED]");
}
