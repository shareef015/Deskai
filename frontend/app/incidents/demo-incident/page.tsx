"use client";

import { useEffect, useState, type ReactNode } from "react";
import { DegradedModeBanner } from "../../../src/components/reliability/DegradedModeBanner";
import { OperatorErrorBoundary } from "../../../src/components/reliability/OperatorErrorBoundary";
import { apiRequest } from "../../../src/lib/reliability/api-client";
import { ConnectivityMonitor, type ConnectivityState } from "../../../src/lib/reliability/connectivity";
import { IncidentSchema, type Incident } from "../../../src/schemas/incident.schema";

const monitor = new ConnectivityMonitor();

function IncidentPanel(): ReactNode {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [connectivity, setConnectivity] = useState<ConnectivityState>("online");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const markOffline = (): void => setConnectivity(monitor.failure(false).state);
    const markOnline = (): void => setConnectivity(monitor.success().state);
    globalThis.addEventListener("offline", markOffline);
    globalThis.addEventListener("online", markOnline);

    void apiRequest("/api/incidents/demo-incident", { method: "GET" }, {
      schema: IncidentSchema,
      signal: controller.signal,
      timeoutMs: 3_000,
    }).then((data) => {
      setIncident(data);
      setConnectivity(monitor.success().state);
    }).catch((requestError: unknown) => {
      if (controller.signal.aborted) return;
      setConnectivity(monitor.failure().state);
      setError(requestError instanceof Error ? requestError.message : "Incident request failed");
    });

    return () => {
      controller.abort(new DOMException("Route unmounted", "AbortError"));
      globalThis.removeEventListener("offline", markOffline);
      globalThis.removeEventListener("online", markOnline);
    };
  }, []);

  return (
    <main id="main-content" tabIndex={-1}>
      <h1>Incident workspace</h1>
      <DegradedModeBanner state={connectivity} />
      {error ? <p role="alert">{error}</p> : null}
      {!incident && !error ? <p role="status">Loading incident…</p> : null}
      {incident ? (
        <section aria-labelledby="incident-title">
          <h2 id="incident-title">{incident.title}</h2>
          <dl>
            <dt>Status</dt><dd>{incident.status}</dd>
            <dt>Severity</dt><dd>{incident.severity}</dd>
          </dl>
          <button type="button" disabled={connectivity !== "online"}>Request remediation</button>
        </section>
      ) : null}
    </main>
  );
}

export default function DemoIncidentPage(): ReactNode {
  return (
    <OperatorErrorBoundary boundary="demo-incident">
      <IncidentPanel />
    </OperatorErrorBoundary>
  );
}
