import { browserCanRender, identityBoundaryRules, requiresFreshAuthentication } from "../../src/lib/identity/authorization-context";
import type { BrowserSession } from "../../src/schemas/identity.schema";

const session: BrowserSession = {
  authenticated: true, userId: "u1", tenantId: "tenant-a", roles: ["approver"],
  capabilities: ["incident:read", "remediation:approve"], issuedAt: 100, expiresAt: 1000, authTime: 100,
  authVersion: 2, permissionVersion: 4, acr: "mfa", amr: ["pwd", "otp"],
};

describe("browser identity trust boundary", () => {
  it("denies cross-tenant rendering", () => {
    expect(browserCanRender(session, { tenantId: "tenant-b", requiredCapability: "remediation:approve" })).toBe(false);
  });

  it("requires recent authentication for sensitive actions", () => {
    expect(requiresFreshAuthentication(session, 500, 300)).toBe(true);
  });

  it("keeps OAuth tokens out of browser storage contracts", () => {
    expect(identityBoundaryRules.accessTokenInBrowserStorage).toBe(false);
    expect(identityBoundaryRules.refreshTokenInBrowserStorage).toBe(false);
    expect(identityBoundaryRules.backendAuthorizationIsAuthoritative).toBe(true);
  });
});
