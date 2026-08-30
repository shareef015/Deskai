export interface TrustedTypePolicyLike {
  createHTML(input: string): unknown;
}

interface TrustedTypesFactoryLike {
  createPolicy(name: string, rules: { createHTML(input: string): string }): TrustedTypePolicyLike;
}

declare global {
  interface Window {
    trustedTypes?: TrustedTypesFactoryLike;
  }
}

let cachedPolicy: TrustedTypePolicyLike | null | undefined;

export function getTrustedHtmlPolicy(sanitize: (html: string) => string): TrustedTypePolicyLike | null {
  if (cachedPolicy !== undefined) return cachedPolicy;
  if (typeof window === "undefined" || !window.trustedTypes) {
    cachedPolicy = null;
    return null;
  }
  cachedPolicy = window.trustedTypes.createPolicy("deskpilot-html", {
    createHTML: (input) => sanitize(input),
  });
  return cachedPolicy;
}
