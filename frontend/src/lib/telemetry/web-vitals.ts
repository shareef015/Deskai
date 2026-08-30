import type { TelemetrySink } from "./frontend-telemetry";

function rating(name: string, value: number): "good" | "needs-improvement" | "poor" {
  const thresholds: Record<string, readonly [number, number]> = {
    LCP: [2500, 4000],
    INP: [200, 500],
    CLS: [0.1, 0.25],
  };
  const pair = thresholds[name];
  if (!pair) return "good";
  return value <= pair[0] ? "good" : value <= pair[1] ? "needs-improvement" : "poor";
}

export function observeWebVitals(sink: TelemetrySink): () => void {
  if (typeof PerformanceObserver === "undefined") return () => undefined;
  const observers: PerformanceObserver[] = [];
  let cls = 0;
  let inp = 0;

  const observe = (
    type: string,
    callback: (entry: PerformanceEntry) => void,
  ): void => {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) callback(entry);
      });
      observer.observe({ type, buffered: true });
      observers.push(observer);
    } catch {
      // Unsupported metric APIs must never break the operator workspace.
    }
  };

  observe("largest-contentful-paint", (entry) => {
    const value = entry.startTime;
    sink.emit({ type: "web_vital", name: "LCP", value, rating: rating("LCP", value) });
  });

  observe("layout-shift", (entry) => {
    const shift = entry as PerformanceEntry & { value?: number; hadRecentInput?: boolean };
    if (shift.hadRecentInput) return;
    cls += shift.value ?? 0;
    sink.emit({ type: "web_vital", name: "CLS", value: cls, rating: rating("CLS", cls) });
  });

  observe("event", (entry) => {
    inp = Math.max(inp, entry.duration);
    sink.emit({ type: "web_vital", name: "INP", value: inp, rating: rating("INP", inp) });
  });

  return () => observers.forEach((observer) => observer.disconnect());
}
