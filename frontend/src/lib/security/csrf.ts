const STATE_CHANGING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export interface CsrfRequestContext {
  readonly method: string;
  readonly origin: string | null;
  readonly expectedOrigin: string;
  readonly csrfCookie: string | null;
  readonly csrfHeader: string | null;
}

export function timingSafeEqualText(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let diff = 0;
  for (let i = 0; i < left.length; i += 1) diff |= left.charCodeAt(i) ^ right.charCodeAt(i);
  return diff === 0;
}

export function validateCsrfRequest(context: CsrfRequestContext): boolean {
  const method = context.method.toUpperCase();
  if (!STATE_CHANGING_METHODS.has(method)) return true;
  if (context.origin !== context.expectedOrigin) return false;
  if (!context.csrfCookie || !context.csrfHeader) return false;
  return timingSafeEqualText(context.csrfCookie, context.csrfHeader);
}

export function attachCsrfHeader(headers: HeadersInit | undefined, csrfToken: string): Headers {
  const output = new Headers(headers);
  output.set("X-CSRF-Token", csrfToken);
  return output;
}
