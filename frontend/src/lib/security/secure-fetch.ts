import { attachCsrfHeader } from "./csrf";

const MUTATING = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export interface SecureFetchOptions extends RequestInit {
  readonly csrfToken?: string;
  readonly expectedOrigin?: string;
}

export function secureRequestInit(input: RequestInfo | URL, options: SecureFetchOptions = {}): RequestInit {
  const method = (options.method ?? "GET").toUpperCase();
  const expectedOrigin = options.expectedOrigin ?? (typeof location !== "undefined" ? location.origin : undefined);
  if (expectedOrigin) {
    const resolved = new URL(typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url, expectedOrigin);
    if (resolved.origin !== expectedOrigin) throw new Error("Cross-origin API request blocked by frontend trust-boundary policy");
  }
  if (MUTATING.has(method) && !options.csrfToken) throw new Error("CSRF token required for state-changing request");
  const headers = MUTATING.has(method) ? attachCsrfHeader(options.headers, options.csrfToken!) : new Headers(options.headers);
  return { ...options, headers, credentials: "same-origin", redirect: "error" };
}

export async function secureFetch(input: RequestInfo | URL, options: SecureFetchOptions = {}): Promise<Response> {
  return fetch(input, secureRequestInit(input, options));
}
