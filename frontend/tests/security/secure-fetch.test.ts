import { secureRequestInit } from "../../src/lib/security/secure-fetch";

describe("secureFetch request policy", () => {
  it("requires CSRF token for mutations", () => {
    expect(() => secureRequestInit("/api/incidents/1", { method: "PATCH", expectedOrigin: "https://deskpilot.example" })).toThrow();
  });
  it("attaches CSRF token and same-origin credentials", () => {
    const init = secureRequestInit("/api/incidents/1", { method: "PATCH", csrfToken: "csrf-1", expectedOrigin: "https://deskpilot.example" });
    expect((init.headers as Headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(init.credentials).toBe("same-origin");
    expect(init.redirect).toBe("error");
  });
  it("blocks cross-origin API targets", () => {
    expect(() => secureRequestInit("https://evil.example/api", { expectedOrigin: "https://deskpilot.example" })).toThrow();
  });
});
