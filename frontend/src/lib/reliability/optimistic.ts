export interface OptimisticTransaction<T> {
  readonly id: string;
  readonly previous: T;
  readonly optimistic: T;
  commit(): void;
  rollback(): T;
}

export function beginOptimisticTransaction<T>(
  previous: T,
  optimistic: T,
  onCommit: (value: T) => void,
  onRollback: (value: T) => void,
): OptimisticTransaction<T> {
  let settled = false;
  const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;
  return {
    id,
    previous,
    optimistic,
    commit(): void {
      if (settled) return;
      settled = true;
      onCommit(optimistic);
    },
    rollback(): T {
      if (!settled) {
        settled = true;
        onRollback(previous);
      }
      return previous;
    },
  };
}
