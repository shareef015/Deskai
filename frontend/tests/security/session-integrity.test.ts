import { assertSessionBinding, isSessionUsable, secureSessionCookieContract } from "../../src/lib/security/session-integrity";

describe("session integrity", () => {
  const now = 1_800_000_000_000;
  const session = { sessionId: "0123456789abcdef", userId: "u1", tenantId: "t1", issuedAt: now - 1_000, expiresAt: now + 60_000, authVersion: 1 };
  it("accepts a live, bound session", () => {
    expect(isSessionUsable(session, now)).toBe(true);
    expect(() => assertSessionBinding(session, "t1", "u1")).not.toThrow();
  });
  it("specifies HttpOnly/Secure browser session cookies", () => {
    expect(secureSessionCookieContract.httpOnly).toBe(true);
    expect(secureSessionCookieContract.secure).toBe(true);
    expect(secureSessionCookieContract.clientReadableAccessToken).toBe(false);
  });
});
