import { ResourceScope } from "../../src/lib/reliability/resource-scope";

describe("ResourceScope", () => {
  afterEach(() => jest.useRealTimers());

  it("drains tracked timers on teardown", () => {
    jest.useFakeTimers();
    const scope = new ResourceScope();
    scope.setInterval(() => undefined, 1_000);
    scope.setTimeout(() => undefined, 5_000);
    expect(scope.activeResources).toBe(2);
    scope.dispose();
    expect(scope.activeResources).toBe(0);
    expect(() => scope.assertDrained()).not.toThrow();
  });

  it("reports resources that were not torn down", () => {
    jest.useFakeTimers();
    const scope = new ResourceScope();
    scope.setInterval(() => undefined, 1_000);
    expect(() => scope.assertDrained()).toThrow(/Resource leak detected/);
    scope.dispose();
  });
});
