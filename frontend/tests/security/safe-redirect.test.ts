import { safeRedirectTarget } from "../../src/lib/security/safe-redirect";

describe("safeRedirectTarget", () => {
  it("keeps local paths", () => expect(safeRedirectTarget("/incidents/42?tab=evidence")).toBe("/incidents/42?tab=evidence"));
  it.each(["https://evil.example", "//evil.example", "/\\evil.example"])("blocks external target %s", (target) => {
    expect(safeRedirectTarget(target, "/home")).toBe("/home");
  });
});
