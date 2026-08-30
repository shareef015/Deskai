import type { BrowserSession } from "../../schemas/identity.schema";

export interface ProtectedResource {
  readonly tenantId: string;
  readonly requiredCapability: string;
}

export function browserCanRender(session: BrowserSession, resource: ProtectedResource): boolean {
  if (!session.authenticated) return false;
  return session.tenantId === resource.tenantId && session.capabilities.includes(resource.requiredCapability);
}

export function requiresFreshAuthentication(session: BrowserSession, nowSeconds: number, maxAgeSeconds = 300): boolean {
  return !session.authenticated || session.authTime < nowSeconds - maxAgeSeconds;
}

export const identityBoundaryRules = Object.freeze({
  backendAuthorizationIsAuthoritative: true,
  accessTokenInBrowserStorage: false,
  refreshTokenInBrowserStorage: false,
  sessionCookieHttpOnly: true,
  denyCrossTenantRender: true,
});
