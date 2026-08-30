export type ResourceDisposer = () => void;

export class ResourceScope {
  private readonly disposers = new Set<ResourceDisposer>();
  private disposed = false;

  add(disposer: ResourceDisposer): ResourceDisposer {
    if (this.disposed) {
      disposer();
      return () => undefined;
    }
    this.disposers.add(disposer);
    return () => {
      if (!this.disposers.delete(disposer)) return;
      disposer();
    };
  }

  addEventListener<K extends keyof WindowEventMap>(
    target: Window,
    type: K,
    listener: (event: WindowEventMap[K]) => void,
  ): ResourceDisposer {
    const wrapped = listener as EventListener;
    target.addEventListener(type, wrapped);
    return this.add(() => target.removeEventListener(type, wrapped));
  }

  setInterval(callback: () => void, intervalMs: number): ResourceDisposer {
    const id = globalThis.setInterval(callback, intervalMs);
    return this.add(() => globalThis.clearInterval(id));
  }

  setTimeout(callback: () => void, delayMs: number): ResourceDisposer {
    let release: ResourceDisposer = () => undefined;
    const id = globalThis.setTimeout(() => {
      release();
      callback();
    }, delayMs);
    release = this.add(() => globalThis.clearTimeout(id));
    return release;
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    for (const dispose of [...this.disposers]) dispose();
    this.disposers.clear();
  }

  get activeResources(): number {
    return this.disposers.size;
  }

  assertDrained(): void {
    if (this.disposers.size !== 0) {
      throw new Error(`Resource leak detected: ${this.disposers.size} frontend resource(s) still active`);
    }
  }
}
