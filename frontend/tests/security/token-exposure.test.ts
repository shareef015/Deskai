import { isCredentialLike } from "../../src/lib/security/token-exposure";

describe("token exposure", () => {
  it("detects bearer strings", () => expect(isCredentialLike("Bearer top-secret")).toBe(true));
  it("does not classify ordinary IDs as credentials", () => expect(isCredentialLike("INC-1042")).toBe(false));
});
