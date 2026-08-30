export type ConnectivityState = "online" | "degraded" | "offline";

export interface ConnectivitySnapshot {
  readonly state: ConnectivityState;
  readonly lastSuccessAt: number | null;
  readonly consecutiveFailures: number;
}

export class ConnectivityMonitor {
  private snapshot: ConnectivitySnapshot = { state: "online", lastSuccessAt: null, consecutiveFailures: 0 };

  success(now = Date.now()): ConnectivitySnapshot {
    this.snapshot = { state: "online", lastSuccessAt: now, consecutiveFailures: 0 };
    return this.snapshot;
  }

  failure(browserOnline = typeof navigator === "undefined" ? true : navigator.onLine): ConnectivitySnapshot {
    const failures = this.snapshot.consecutiveFailures + 1;
    const state: ConnectivityState = !browserOnline ? "offline" : failures >= 2 ? "degraded" : this.snapshot.state;
    this.snapshot = { ...this.snapshot, state, consecutiveFailures: failures };
    return this.snapshot;
  }

  current(): ConnectivitySnapshot {
    return this.snapshot;
  }
}
