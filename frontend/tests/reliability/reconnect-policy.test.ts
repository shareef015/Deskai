import { reconnectDelay } from "../../src/lib/reliability/reconnect-policy";

describe("reconnectDelay", () => {
  it("is exponential, capped and bounded", () => {
    expect(reconnectDelay(1)).toBe(500);
    expect(reconnectDelay(2)).toBe(1_000);
    expect(reconnectDelay(10)).toBe(15_000);
    expect(reconnectDelay(13)).toBeNull();
  });
});
