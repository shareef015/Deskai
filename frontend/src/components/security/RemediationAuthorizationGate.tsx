import type { ReactNode } from "react";
import type { BrowserSession } from "../../schemas/identity.schema";
import { browserCanRender } from "../../lib/identity/authorization-context";

interface Props {
  session: BrowserSession;
  tenantId: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function RemediationAuthorizationGate({ session, tenantId, children, fallback = null }: Props) {
  const allowed = browserCanRender(session, { tenantId, requiredCapability: "remediation:approve" });
  return allowed ? <>{children}</> : <>{fallback}</>;
}
