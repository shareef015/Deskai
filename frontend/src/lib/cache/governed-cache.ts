export interface CacheIdentity {
  readonly tenantId: string;
  readonly userId: string;
  readonly route: string;
  readonly configFingerprint: string;
  readonly schemaVersion: string;
}

interface CacheEntry<T> {
  readonly value: T;
  readonly createdAt: number;
  readonly expiresAt: number;
}

export class GovernedMemoryCache {
  private readonly entries = new Map<string, CacheEntry<unknown>>();

  key(identity: CacheIdentity): string {
    return JSON.stringify([
      identity.tenantId,
      identity.userId,
      identity.route,
      identity.configFingerprint,
      identity.schemaVersion,
    ]);
  }

  get<T>(identity: CacheIdentity, now = Date.now()): T | undefined {
    const key = this.key(identity);
    const entry = this.entries.get(key);
    if (!entry) return undefined;
    if (entry.expiresAt <= now) {
      this.entries.delete(key);
      return undefined;
    }
    return entry.value as T;
  }

  set<T>(identity: CacheIdentity, value: T, ttlMs: number, now = Date.now()): void {
    if (!Number.isFinite(ttlMs) || ttlMs <= 0) throw new Error("ttlMs must be positive");
    this.entries.set(this.key(identity), { value, createdAt: now, expiresAt: now + ttlMs });
  }

  invalidateTenant(tenantId: string): void {
    for (const [key] of this.entries) {
      try {
        const parsed = JSON.parse(key) as unknown;
        if (Array.isArray(parsed) && parsed[0] === tenantId) this.entries.delete(key);
      } catch {
        this.entries.delete(key);
      }
    }
  }

  invalidateConfig(configFingerprint: string): void {
    for (const [key] of this.entries) {
      try {
        const parsed = JSON.parse(key) as unknown;
        if (Array.isArray(parsed) && parsed[3] === configFingerprint) this.entries.delete(key);
      } catch {
        this.entries.delete(key);
      }
    }
  }

  clear(): void {
    this.entries.clear();
  }
}
