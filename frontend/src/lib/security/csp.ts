export interface CspOptions {
  readonly nonce: string;
  readonly isDevelopment?: boolean;
  readonly connectSources?: readonly string[];
}

function join(values: readonly string[]): string {
  return values.join(" ");
}

export function buildContentSecurityPolicy(options: CspOptions): string {
  const connect = ["'self'", ...(options.connectSources ?? [])];
  const directives = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${options.nonce}' 'strict-dynamic'${options.isDevelopment ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'nonce-${options.nonce}'${options.isDevelopment ? " 'unsafe-inline'" : ""}`,
    "img-src 'self' blob: data:",
    "font-src 'self'",
    `connect-src ${join(connect)}`,
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "manifest-src 'self'",
    "media-src 'self'",
    "require-trusted-types-for 'script'",
    "trusted-types deskpilot-html deskpilot-markdown",
    "upgrade-insecure-requests",
  ];
  return directives.map((entry) => `${entry};`).join(" ");
}

export const securityResponseHeaders: Readonly<Record<string, string>> = Object.freeze({
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), bluetooth=(), browsing-topics=()",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "X-Permitted-Cross-Domain-Policies": "none",
  "X-XSS-Protection": "0",
});
