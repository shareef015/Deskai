import type { ReactNode } from "react";
import type { ConnectivityState } from "../../lib/reliability/connectivity";

export function DegradedModeBanner({ state }: { readonly state: ConnectivityState }): ReactNode {
  if (state === "online") return null;
  const text = state === "offline"
    ? "You are offline. Read-only cached information may be shown; remediation actions are disabled."
    : "Connection is degraded. Live updates may be delayed; high-risk actions require a fresh server confirmation.";
  return <div role="status" aria-live="polite" data-connectivity={state}>{text}</div>;
}
