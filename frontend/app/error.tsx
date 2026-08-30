"use client";

import { useEffect, type ReactNode } from "react";

export default function GlobalRouteError({
  error,
  reset,
}: {
  readonly error: Error & { digest?: string };
  readonly reset: () => void;
}): ReactNode {
  useEffect(() => {
    // In production, emit only the safe error classification/correlation metadata.
    console.error("DeskPilot route boundary", { name: error.name, digest: error.digest });
  }, [error]);

  return (
    <main id="main-content" tabIndex={-1}>
      <h1>Workspace recovery required</h1>
      <p>The current page failed to render. No remediation action should be assumed successful.</p>
      <button type="button" onClick={reset}>Retry page</button>
    </main>
  );
}
