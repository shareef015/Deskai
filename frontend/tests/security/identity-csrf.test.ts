import { readCsrfToken } from "../../src/lib/identity/csrf-token";

describe("identity CSRF token bridge", () => {
  it("reads only the dedicated CSRF cookie", () => {
    expect(readCsrfToken("other=x; __Host-deskpilot_csrf=abc%2E123; session=secret")).toBe("abc.123");
  });

  it("returns null when the CSRF cookie is absent", () => {
    expect(readCsrfToken("other=x")).toBeNull();
  });
});
