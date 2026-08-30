const CSRF_COOKIE_NAME = "__Host-deskpilot_csrf";

export function readCsrfToken(cookieHeader?: string): string | null {
  const source = cookieHeader ?? (typeof document !== "undefined" ? document.cookie : "");
  for (const part of source.split(";")) {
    const [rawName, ...rawValue] = part.trim().split("=");
    if (rawName === CSRF_COOKIE_NAME) return decodeURIComponent(rawValue.join("="));
  }
  return null;
}

export function requireCsrfToken(): string {
  const token = readCsrfToken();
  if (!token) throw new Error("CSRF cookie is missing");
  return token;
}
