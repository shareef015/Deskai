import { redactSensitive, scrubText } from "./redaction";

export type BrowserThreatEvent =
  | { type: "csp_violation"; directive: string; blockedUri: string }
  | { type: "csrf_rejected"; route: string }
  | { type: "authorization_denied"; capability: string; route: string }
  | { type: "unsafe_redirect_blocked"; target: string }
  | { type: "upload_rejected"; reason: string; fileType: string }
  | { type: "session_binding_failure"; route: string };

export interface BrowserThreatSink {
  emit(event: BrowserThreatEvent): void;
}

export function safeThreatEvent(event: BrowserThreatEvent): BrowserThreatEvent {
  const sanitized = redactSensitive(event);
  if (sanitized.type === "csp_violation") return { ...sanitized, blockedUri: scrubText(sanitized.blockedUri).slice(0, 512) };
  if (sanitized.type === "unsafe_redirect_blocked") return { ...sanitized, target: scrubText(sanitized.target).slice(0, 512) };
  return sanitized;
}

export function installCspViolationReporter(sink: BrowserThreatSink): () => void {
  const handler = (event: SecurityPolicyViolationEvent): void => {
    sink.emit(safeThreatEvent({
      type: "csp_violation",
      directive: event.effectiveDirective,
      blockedUri: event.blockedURI || "unknown",
    }));
  };
  globalThis.addEventListener("securitypolicyviolation", handler as EventListener);
  return () => globalThis.removeEventListener("securitypolicyviolation", handler as EventListener);
}
