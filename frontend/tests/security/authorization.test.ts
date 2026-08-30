import { canAccess, type Principal } from "../../src/lib/security/authorization";

describe("frontend authorization guard", () => {
  const principal: Principal = { userId: "u1", tenantId: "t1", capabilities: new Set(["incident:read"]) };
  it("requires both tenant binding and capability", () => {
    expect(canAccess(principal, { tenantId: "t1", required: "incident:read" })).toBe(true);
    expect(canAccess(principal, { tenantId: "t2", required: "incident:read" })).toBe(false);
    expect(canAccess(principal, { tenantId: "t1", required: "remediation:approve" })).toBe(false);
  });
});
