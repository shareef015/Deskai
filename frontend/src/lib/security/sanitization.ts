const SAFE_PROTOCOLS = new Set(["http:", "https:", "mailto:"]);

export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function sanitizeUrl(raw: string, base = "https://deskpilot.invalid"): string | null {
  try {
    const parsed = new URL(raw, base);
    if (!SAFE_PROTOCOLS.has(parsed.protocol)) return null;
    if (parsed.username || parsed.password) return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

export function assertPlainText(value: string): string {
  if (/[<>]/.test(value)) throw new Error("Raw HTML is not allowed in this field");
  return value;
}
