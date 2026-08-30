import type { ReactElement } from "react";

export default function HomePage(): ReactElement {
  return (
    <main id="main-content" tabIndex={-1}>
      <h1>DeskPilot AI</h1>
      <p>Frontend reliability demonstration workspace.</p>
      <a href="/incidents/demo-incident">Open demo incident</a>
    </main>
  );
}
