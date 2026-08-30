export type BrowserTraceHeaders = Readonly<{
  traceparent?: string;
  "x-correlation-id": string;
}>;

const TRACEPARENT = /^00-[a-f0-9]{32}-[a-f0-9]{16}-(00|01)$/;

function randomHex(bytes: number): string {
  const buffer = new Uint8Array(bytes);
  crypto.getRandomValues(buffer);
  const value = Array.from(buffer, (b) => b.toString(16).padStart(2, "0")).join("");
  return /^0+$/.test(value) ? randomHex(bytes) : value;
}

export function createBrowserTraceparent(sampled = true): string {
  return `00-${randomHex(16)}-${randomHex(8)}-${sampled ? "01" : "00"}`;
}

export function governedTraceHeaders(correlationId: string, traceparent?: string): BrowserTraceHeaders {
  const normalized = correlationId.trim();
  if (!normalized || normalized.length > 128) throw new Error("invalid_correlation_id");
  if (traceparent !== undefined && !TRACEPARENT.test(traceparent)) throw new Error("invalid_traceparent");
  return traceparent
    ? { traceparent, "x-correlation-id": normalized }
    : { "x-correlation-id": normalized };
}
