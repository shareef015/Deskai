import type { AnchorHTMLAttributes, ReactNode } from "react";
import { sanitizeUrl } from "../../lib/security/sanitization";

interface Props extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> {
  readonly href: string;
  readonly children: ReactNode;
}

export function SafeExternalLink({ href, children, rel, target = "_blank", ...rest }: Props) {
  const safe = sanitizeUrl(href);
  if (!safe) return <span>{children}</span>;
  return <a {...rest} href={safe} target={target} rel={rel ?? "noopener noreferrer"}>{children}</a>;
}
