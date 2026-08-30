import { RequestManager } from "../../src/lib/reliability/request-manager";

describe("RequestManager", () => {
  it("aborts an older request with the same key", () => {
    const manager = new RequestManager();
    const first = manager.begin("incident:123");
    const second = manager.begin("incident:123");
    expect(first.aborted).toBe(true);
    expect(second.aborted).toBe(false);
    expect(manager.activeCount).toBe(1);
  });

  it("cancels every active request on route teardown", () => {
    const manager = new RequestManager();
    const one = manager.begin("one");
    const two = manager.begin("two");
    manager.cancelAll();
    expect(one.aborted).toBe(true);
    expect(two.aborted).toBe(true);
    expect(manager.activeCount).toBe(0);
  });
});
