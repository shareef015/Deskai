import { assertPlainText, escapeHtml, sanitizeUrl } from "../../src/lib/security/sanitization";

describe("XSS sink governance", () => {
  it("escapes markup", () => expect(escapeHtml('<img src=x onerror="alert(1)">')).not.toContain("<img"));
  it("blocks javascript URLs", () => expect(sanitizeUrl("javascript:alert(1)")).toBeNull());
  it("rejects raw markup for plain-text fields", () => expect(() => assertPlainText("<script>x</script>")).toThrow());
});
