export interface SessionSnapshot {
  readonly sessionId: string;
  readonly userId: string;
  readonly tenantId: string;
  readonly issuedAt: number;
  readonly expiresAt: number;
  readonly authVersion: number;
}

export function isSessionUsable(session: SessionSnapshot, now = Date.now()): boolean {
  return session.sessionId.length >= 16
    && session.userId.length > 0
    && session.tenantId.length > 0
    && session.issuedAt <= now
    && session.expiresAt > now
    && session.authVersion > 0;
}

export function assertSessionBinding(current: SessionSnapshot, expectedTenantId: string, expectedUserId: string): void {
  if (!isSessionUsable(current)) throw new Error("Session expired or invalid");
  if (current.tenantId !== expectedTenantId || current.userId !== expectedUserId) {
    throw new Error("Session identity binding mismatch");
  }
}

export const secureSessionCookieContract = Object.freeze({
  httpOnly: true,
  secure: true,
  sameSite: "lax" as const,
  path: "/",
  clientReadableAccessToken: false,
});
