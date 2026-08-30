"use client";

import { useMemo, useState, type ReactNode } from "react";
import type { DemoPersona, DemoRunState, DemoScenario } from "../../src/contracts/demo.contract";

const DEFAULT_PERSONA: DemoPersona = { personaId: "service-desk-demo", displayName: "Service Desk Engineer", role: "service_desk_engineer", tenantId: "tenant-a", synthetic: true };

const PERSONAS: readonly DemoPersona[] = [
  { personaId: "recruiter-demo", displayName: "Recruiter Demo Viewer", role: "recruiter", tenantId: "tenant-a", synthetic: true },
  DEFAULT_PERSONA,
  { personaId: "approver-demo", displayName: "Remediation Approver", role: "approver", tenantId: "tenant-a", synthetic: true },
  { personaId: "reviewer-demo", displayName: "Security Reviewer", role: "reviewer", tenantId: "tenant-a", synthetic: true },
];

const DEFAULT_SCENARIO: DemoScenario = { scenarioId: "DEMO-PRINTER-QUEUE", label: "Printer queue stuck", domain: "printer", expected: "closed" };

const SCENARIOS: readonly DemoScenario[] = [
  DEFAULT_SCENARIO,
  { scenarioId: "DEMO-PRINTER-OFFLINE", label: "Printer offline", domain: "printer", expected: "closed" },
  { scenarioId: "DEMO-OUTLOOK-DISCONNECTED", label: "Outlook disconnected", domain: "outlook", expected: "closed" },
  { scenarioId: "DEMO-OUTLOOK-CRASH", label: "Outlook crashes", domain: "outlook", expected: "closed" },
  { scenarioId: "DEMO-VERIFY-FAIL", label: "Verification failure", domain: "printer", expected: "diagnosing" },
  { scenarioId: "DEMO-CROSS-TENANT", label: "Cross-tenant access attempt", domain: "printer", expected: "denied" },
];

const NORMAL_FLOW: readonly DemoRunState[] = ["greeting", "intake", "retrieval", "diagnosis", "approval", "remediation", "verification", "closed"];
const VERIFY_FAIL_FLOW: readonly DemoRunState[] = ["greeting", "intake", "retrieval", "diagnosis", "approval", "remediation", "verification", "diagnosing"];
const DENIED_FLOW: readonly DemoRunState[] = ["greeting", "intake", "denied"];

function flowFor(scenario: DemoScenario): readonly DemoRunState[] {
  if (scenario.expected === "denied") return DENIED_FLOW;
  if (scenario.expected === "diagnosing") return VERIFY_FAIL_FLOW;
  return NORMAL_FLOW;
}

function stateLabel(state: DemoRunState): string {
  return state.replaceAll("_", " ").replace(/^./, (value) => value.toUpperCase());
}

export default function RecruiterDemoPage(): ReactNode {
  const [personaId, setPersonaId] = useState("service-desk-demo");
  const [scenarioId, setScenarioId] = useState("DEMO-PRINTER-QUEUE");
  const [state, setState] = useState<DemoRunState>("ready");
  const [history, setHistory] = useState<DemoRunState[]>([]);
  const [resetCount, setResetCount] = useState(0);

  const persona = useMemo(() => PERSONAS.find((item) => item.personaId === personaId) ?? DEFAULT_PERSONA, [personaId]);
  const scenario = useMemo(() => SCENARIOS.find((item) => item.scenarioId === scenarioId) ?? DEFAULT_SCENARIO, [scenarioId]);

  const runScenario = (): void => {
    const flow = flowFor(scenario);
    setHistory([...flow]);
    setState(flow.at(-1) ?? "ready");
  };

  const resetDemo = (): void => {
    setState("ready");
    setHistory([]);
    setPersonaId("service-desk-demo");
    setScenarioId("DEMO-PRINTER-QUEUE");
    setResetCount((value) => value + 1);
  };

  return (
    <main id="main-content" tabIndex={-1} style={{ maxWidth: "76rem", margin: "0 auto", padding: "var(--space-6)" }}>
      <header>
        <p><strong>Recruiter-safe synthetic environment</strong></p>
        <h1>DeskPilot AI — End-to-End Service Desk Demo</h1>
        <p>Hi, good day. Welcome to DeskPilot AI Service Desk.</p>
        <p><strong>How can I help you today?</strong></p>
        <p>This workspace uses synthetic personas, devices, incidents and remediation results only.</p>
      </header>

      <section aria-labelledby="demo-controls" style={{ display: "grid", gap: "var(--space-4)", marginBlock: "var(--space-6)" }}>
        <h2 id="demo-controls">Demo controls</h2>
        <label htmlFor="demo-persona">Synthetic persona</label>
        <select id="demo-persona" value={personaId} onChange={(event) => setPersonaId(event.target.value)}>
          {PERSONAS.map((item) => <option key={item.personaId} value={item.personaId}>{item.displayName}</option>)}
        </select>

        <label htmlFor="demo-scenario">Scenario</label>
        <select id="demo-scenario" value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
          {SCENARIOS.map((item) => <option key={item.scenarioId} value={item.scenarioId}>{item.label}</option>)}
        </select>

        <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <button type="button" onClick={runScenario}>Run certified scenario</button>
          <button type="button" onClick={resetDemo}>Reset demo</button>
        </div>
      </section>

      <section aria-labelledby="selected-context">
        <h2 id="selected-context">Selected context</h2>
        <dl>
          <dt>Persona</dt><dd>{persona.displayName}</dd>
          <dt>Tenant</dt><dd>{persona.tenantId}</dd>
          <dt>Scenario</dt><dd>{scenario.label}</dd>
          <dt>Domain</dt><dd>{scenario.domain}</dd>
          <dt>Expected terminal state</dt><dd>{scenario.expected}</dd>
        </dl>
      </section>

      <section aria-labelledby="run-status" style={{ marginBlock: "var(--space-6)" }}>
        <h2 id="run-status">Execution status</h2>
        <p role="status" aria-live="polite" data-testid="demo-terminal-state">{stateLabel(state)}</p>
        {state === "denied" ? <p role="alert">Cross-tenant request denied before retrieval or tool execution.</p> : null}
        {state === "diagnosing" ? <p role="status">Verification failed. Incident returned to diagnosis and was not falsely closed.</p> : null}
        {state === "closed" ? <p role="status">Verification passed. Incident closed with evidence, approval and audit events.</p> : null}
      </section>

      <section aria-labelledby="journey-heading">
        <h2 id="journey-heading">Certified journey</h2>
        {history.length === 0 ? <p>No scenario has run yet.</p> : (
          <ol>
            {history.map((item, index) => <li key={`${item}-${index}`}>{stateLabel(item)}</li>)}
          </ol>
        )}
      </section>

      <aside aria-labelledby="trust-heading" style={{ marginBlockStart: "var(--space-6)" }}>
        <h2 id="trust-heading">Trust boundaries demonstrated</h2>
        <ul>
          <li>Tenant-safe RAG and citation grounding</li>
          <li>Deterministic LangGraph-style state transitions</li>
          <li>Read-only MCP diagnostics before remediation</li>
          <li>Human approval before mutating tools</li>
          <li>Independent verification before closure</li>
          <li>Prompt-injection and cross-tenant containment</li>
          <li>Deterministic environment reset after recruiter demos</li>
        </ul>
        <p data-testid="demo-reset-count">Reset count: {resetCount}</p>
      </aside>
    </main>
  );
}
