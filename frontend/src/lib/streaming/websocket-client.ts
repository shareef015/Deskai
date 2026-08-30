export type SocketState = "idle" | "connecting" | "open" | "reconnecting" | "closed";

export interface ResilientWebSocketOptions {
  readonly url: string;
  readonly protocols?: string | string[];
  readonly heartbeatMs?: number;
  readonly pongTimeoutMs?: number;
  readonly maxReconnects?: number;
  readonly onMessage: (event: MessageEvent<string>) => void;
  readonly onStateChange?: (state: SocketState) => void;
}

export class ResilientWebSocketClient {
  private socket: WebSocket | null = null;
  private reconnects = 0;
  private heartbeatTimer: number | null = null;
  private pongTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private stopped = false;

  constructor(private readonly options: ResilientWebSocketOptions) {}

  start(): void {
    this.stopped = false;
    this.connect();
  }

  stop(): void {
    this.stopped = true;
    this.clearTimers();
    this.socket?.close(1000, "client shutdown");
    this.socket = null;
    this.transition("closed");
  }

  send(payload: string): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) return false;
    this.socket.send(payload);
    return true;
  }

  private connect(): void {
    if (this.stopped) return;
    this.transition(this.reconnects === 0 ? "connecting" : "reconnecting");
    const socket = new WebSocket(this.options.url, this.options.protocols);
    this.socket = socket;
    socket.onopen = () => {
      this.reconnects = 0;
      this.transition("open");
      this.startHeartbeat(socket);
    };
    socket.onmessage = (event) => {
      if (this.isPong(event.data)) {
        if (this.pongTimer !== null) globalThis.clearTimeout(this.pongTimer);
        this.pongTimer = null;
        return;
      }
      this.options.onMessage(event as MessageEvent<string>);
    };
    socket.onerror = () => socket.close();
    socket.onclose = () => this.scheduleReconnect();
  }

  private startHeartbeat(socket: WebSocket): void {
    const heartbeatMs = this.options.heartbeatMs ?? 20_000;
    const pongTimeoutMs = this.options.pongTimeoutMs ?? 8_000;
    this.heartbeatTimer = globalThis.setInterval(() => {
      if (socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({ type: "ping", at: Date.now() }));
      if (this.pongTimer !== null) globalThis.clearTimeout(this.pongTimer);
      this.pongTimer = globalThis.setTimeout(() => socket.close(4000, "heartbeat timeout"), pongTimeoutMs);
    }, heartbeatMs);
  }

  private isPong(data: unknown): boolean {
    if (typeof data !== "string") return false;
    try {
      const parsed = JSON.parse(data) as unknown;
      return typeof parsed === "object" && parsed !== null && "type" in parsed && (parsed as { type?: unknown }).type === "pong";
    } catch {
      return false;
    }
  }

  private scheduleReconnect(): void {
    this.clearHeartbeatTimers();
    if (this.stopped) return;
    const max = this.options.maxReconnects ?? 10;
    if (this.reconnects >= max) {
      this.transition("closed");
      return;
    }
    this.reconnects += 1;
    this.transition("reconnecting");
    const delay = Math.min(10_000, 400 * 2 ** Math.min(5, this.reconnects - 1));
    this.reconnectTimer = globalThis.setTimeout(() => this.connect(), delay);
  }

  private clearHeartbeatTimers(): void {
    if (this.heartbeatTimer !== null) globalThis.clearInterval(this.heartbeatTimer);
    if (this.pongTimer !== null) globalThis.clearTimeout(this.pongTimer);
    this.heartbeatTimer = null;
    this.pongTimer = null;
  }

  private clearTimers(): void {
    this.clearHeartbeatTimers();
    if (this.reconnectTimer !== null) globalThis.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
  }

  private transition(next: SocketState): void {
    this.options.onStateChange?.(next);
  }
}
