import { z } from "zod";

export interface SseEnvelope<T> {
  readonly id: string;
  readonly event: string;
  readonly data: T;
}

export interface ResilientSseOptions<T> {
  readonly url: string;
  readonly schema: z.ZodType<T>;
  readonly onEvent: (event: SseEnvelope<T>) => void;
  readonly onStateChange?: (state: "connecting" | "open" | "reconnecting" | "closed") => void;
  readonly onContractError?: (error: z.ZodError | SyntaxError) => void;
  readonly maxReconnects?: number;
  readonly baseReconnectMs?: number;
  readonly getLastEventId?: () => string | null;
  readonly persistLastEventId?: (id: string) => void;
}

export class ResilientSseClient<T> {
  private source: EventSource | null = null;
  private reconnects = 0;
  private reconnectTimer: number | null = null;
  private stopped = false;
  private readonly seenEventIds = new Set<string>();

  constructor(private readonly options: ResilientSseOptions<T>) {}

  start(): void {
    this.stopped = false;
    this.connect();
  }

  stop(): void {
    this.stopped = true;
    if (this.reconnectTimer !== null) globalThis.clearTimeout(this.reconnectTimer);
    this.source?.close();
    this.source = null;
    this.options.onStateChange?.("closed");
  }

  private connect(): void {
    if (this.stopped) return;
    this.options.onStateChange?.(this.reconnects === 0 ? "connecting" : "reconnecting");
    const lastId = this.options.getLastEventId?.();
    const baseOrigin = typeof window === "undefined" ? "http://localhost" : window.location.origin;
    const url = new URL(this.options.url, baseOrigin);
    if (lastId) url.searchParams.set("lastEventId", lastId);

    const source = new EventSource(url.toString(), { withCredentials: true });
    this.source = source;
    source.onopen = () => {
      this.reconnects = 0;
      this.options.onStateChange?.("open");
    };
    source.onmessage = (message: MessageEvent<string>) => {
      try {
        const raw: unknown = JSON.parse(message.data);
        const data = this.options.schema.parse(raw);
        const id = message.lastEventId || `${Date.now()}`;
        if (this.seenEventIds.has(id)) return;
        this.seenEventIds.add(id);
        if (this.seenEventIds.size > 2_000) this.seenEventIds.clear();
        this.options.persistLastEventId?.(id);
        this.options.onEvent({ id, event: message.type || "message", data });
      } catch (error: unknown) {
        if (error instanceof z.ZodError || error instanceof SyntaxError) this.options.onContractError?.(error);
        else throw error;
      }
    };
    source.onerror = () => {
      source.close();
      if (this.stopped) return;
      const maxReconnects = this.options.maxReconnects ?? 12;
      if (this.reconnects >= maxReconnects) {
        this.stop();
        return;
      }
      this.reconnects += 1;
      const base = this.options.baseReconnectMs ?? 500;
      const delay = Math.min(15_000, base * 2 ** Math.min(this.reconnects - 1, 5));
      this.reconnectTimer = globalThis.setTimeout(() => this.connect(), delay);
    };
  }
}
