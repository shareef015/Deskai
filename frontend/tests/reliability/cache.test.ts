import { GovernedMemoryCache } from "../../src/lib/cache/governed-cache";

const identity = {
  tenantId: "tenant-a",
  userId: "operator-1",
  route: "/incidents/1",
  configFingerprint: "cfg-1",
  schemaVersion: "v1",
};

describe("GovernedMemoryCache", () => {
  it("expires entries deterministically", () => {
    const cache = new GovernedMemoryCache();
    cache.set(identity, { ok: true }, 100, 1_000);
    expect(cache.get(identity, 1_050)).toEqual({ ok: true });
    expect(cache.get(identity, 1_101)).toBeUndefined();
  });

  it("does not reuse values across tenants", () => {
    const cache = new GovernedMemoryCache();
    cache.set(identity, "secret", 10_000, 1_000);
    expect(cache.get({ ...identity, tenantId: "tenant-b" }, 1_100)).toBeUndefined();
  });
});
