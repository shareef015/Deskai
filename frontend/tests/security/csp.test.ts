import { buildContentSecurityPolicy, securityResponseHeaders } from "../../src/lib/security/csp";

describe("CSP", () => {
  it("enforces nonce scripts, framing denial and Trusted Types", () => {
    const policy = buildContentSecurityPolicy({ nonce: "abc123" });
    expect(policy).toContain("script-src 'self' 'nonce-abc123' 'strict-dynamic'");
    expect(policy).toContain("frame-ancestors 'none'");
    expect(policy).toContain("object-src 'none'");
    expect(policy).toContain("require-trusted-types-for 'script'");
    expect(policy).not.toContain("'unsafe-inline'");
    expect(policy).not.toContain("'unsafe-eval'");
  });

  it("ships clickjacking and MIME-sniffing defenses", () => {
    expect(securityResponseHeaders["X-Frame-Options"]).toBe("DENY");
    expect(securityResponseHeaders["X-Content-Type-Options"]).toBe("nosniff");
  });
});
