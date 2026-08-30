export class RequestManager {
  private readonly controllers = new Map<string, AbortController>();

  begin(key: string): AbortSignal {
    this.cancel(key, new DOMException("Superseded by a newer request", "AbortError"));
    const controller = new AbortController();
    this.controllers.set(key, controller);
    return controller.signal;
  }

  finish(key: string, signal: AbortSignal): void {
    const current = this.controllers.get(key);
    if (current?.signal === signal) this.controllers.delete(key);
  }

  cancel(key: string, reason?: unknown): void {
    const controller = this.controllers.get(key);
    if (!controller) return;
    controller.abort(reason);
    this.controllers.delete(key);
  }

  cancelAll(reason: unknown = new DOMException("Navigation changed", "AbortError")): void {
    for (const controller of this.controllers.values()) controller.abort(reason);
    this.controllers.clear();
  }

  get activeCount(): number {
    return this.controllers.size;
  }
}
