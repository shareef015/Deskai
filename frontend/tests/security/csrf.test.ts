import { validateCsrfRequest } from "../../src/lib/security/csrf";

const base = {
  expectedOrigin: "https://deskpilot.example",
  csrfCookie: "token-123456789",
  csrfHeader: "token-123456789",
};

describe("CSRF validation", () => {
  it("accepts same-origin matching-token state changes", () => {
    expect(validateCsrfRequest({ ...base, method: "POST", origin: base.expectedOrigin })).toBe(true);
  });
  it("rejects cross-origin requests", () => {
    expect(validateCsrfRequest({ ...base, method: "POST", origin: "https://evil.example" })).toBe(false);
  });
  it("rejects missing token", () => {
    expect(validateCsrfRequest({ ...base, method: "DELETE", origin: base.expectedOrigin, csrfHeader: null })).toBe(false);
  });
});
