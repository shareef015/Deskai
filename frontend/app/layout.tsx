import type { ReactElement, ReactNode } from "react";
import { SkipLink } from "../src/components/accessibility/SkipLink";
import "../src/styles/globals.css";

export default function RootLayout({ children }: { readonly children: ReactNode }): ReactElement {
  return (
    <html lang="en">
      <body>
        <SkipLink />
        {children}
      </body>
    </html>
  );
}
