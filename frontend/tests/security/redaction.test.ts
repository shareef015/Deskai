import { redactSensitive, scrubText } from "../../src/lib/security/redaction";

describe("redaction", () => {
  it("redacts nested credentials", () => {
    const value = redactSensitive({ user: "u1", auth: { access_token: "secret", note: "ok" } });
    expect(value.auth.access_token).toBe("[REDACTED]");
    expect(value.auth.note).toBe("ok");
  });
  it("scrubs bearer tokens from text", () => {
    expect(scrubText("Authorization: Bearer abc.def.ghi")).not.toContain("abc.def.ghi");
  });
});
