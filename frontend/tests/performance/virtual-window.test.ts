import { calculateVirtualWindow } from "../../src/lib/performance/virtual-window";

describe("calculateVirtualWindow", () => {
  it("renders a bounded window for large incident lists", () => {
    const result = calculateVirtualWindow({ itemCount: 100_000, itemHeight: 40, viewportHeight: 400, scrollTop: 20_000, overscan: 5 });
    expect(result.endIndex - result.startIndex).toBeLessThanOrEqual(20);
    expect(result.totalHeight).toBe(4_000_000);
  });
});
