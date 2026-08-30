export interface UploadCandidate {
  readonly name: string;
  readonly type: string;
  readonly size: number;
}

const ALLOWED_TYPES = new Set(["application/pdf", "image/png", "image/jpeg", "text/plain"]);
const DANGEROUS_EXTENSIONS = /\.(?:exe|msi|cmd|bat|com|scr|ps1|js|mjs|html?|svg|jar|lnk)$/i;

export interface UploadPolicy {
  readonly maxBytes: number;
  readonly allowedTypes: ReadonlySet<string>;
}

export const DEFAULT_UPLOAD_POLICY: UploadPolicy = {
  maxBytes: 10 * 1024 * 1024,
  allowedTypes: ALLOWED_TYPES,
};

export function validateUpload(candidate: UploadCandidate, policy = DEFAULT_UPLOAD_POLICY): readonly string[] {
  const errors: string[] = [];
  if (!candidate.name || candidate.name.includes("/") || candidate.name.includes("\\") || candidate.name.includes("\0")) errors.push("unsafe_filename");
  if (DANGEROUS_EXTENSIONS.test(candidate.name)) errors.push("dangerous_extension");
  if (!policy.allowedTypes.has(candidate.type)) errors.push("unsupported_mime_type");
  if (candidate.size <= 0 || candidate.size > policy.maxBytes) errors.push("invalid_size");
  return errors;
}

export function safeDownloadFilename(raw: string): string {
  const cleaned = raw.replace(/[\r\n"\\/<>:*?|\x00-\x1F]/g, "_").replace(/\.+$/g, "").trim();
  return (cleaned || "download").slice(0, 120);
}
