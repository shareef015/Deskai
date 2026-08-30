import type { ReactNode } from "react";
import { canAccess, type Principal, type ResourceScope } from "../../lib/security/authorization";

export interface AuthorizationGateProps {
  readonly principal: Principal | null;
  readonly resource: ResourceScope;
  readonly fallback?: ReactNode;
  readonly children: ReactNode;
}

export function AuthorizationGate({ principal, resource, fallback = null, children }: AuthorizationGateProps) {
  return canAccess(principal, resource) ? <>{children}</> : <>{fallback}</>;
}
