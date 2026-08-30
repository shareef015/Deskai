const quality = [
  ["Groundedness", "≥ 95%"],
  ["Citation integrity", "100%"],
  ["Agent route accuracy", "≥ 95%"],
  ["MCP tool success", "≥ 95%"],
  ["Prompt-injection block rate", "100%"],
  ["Hallucination rate", "≤ 2%"],
  ["p95 AI latency", "≤ 5 s"],
  ["Average AI cost", "≤ $0.05/run"],
] as const;

export default function ObservabilityPage() {
  return (
    <main id="main-content" style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
      <h1>AI Quality & Observability</h1>
      <p>Production release thresholds for the governed RAG → agent → MCP execution path.</p>
      <section aria-labelledby="quality-thresholds">
        <h2 id="quality-thresholds">Release quality thresholds</h2>
        <dl>
          {quality.map(([name, value]) => (
            <div key={name} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "1rem", padding: ".75rem 0", borderBottom: "1px solid var(--border)" }}>
              <dt>{name}</dt><dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </main>
  );
}
