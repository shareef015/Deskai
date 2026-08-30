export type FrontendTelemetryEvent =
  | { type: "api_failure"; route: string; status?: number; requestId?: string }
  | { type: "stream_reconnect"; stream: string; attempt: number }
  | { type: "contract_violation"; contract: string; issueCount: number }
  | { type: "ui_error_boundary"; boundary: string; message: string }
  | { type: "session_recovered"; route: string }
  | { type: "ai_trace_link"; correlationId: string; traceparent?: string; stage: "frontend" | "api" | "rag" | "langgraph" | "llm" | "mcp" | "hitl" | "remediation" }
  | { type: "web_vital"; name: string; value: number; rating: "good" | "needs-improvement" | "poor" };

export interface TelemetrySink {
  emit(event: FrontendTelemetryEvent): void;
}

export function createBufferedTelemetrySink(flush: (events: readonly FrontendTelemetryEvent[]) => void, maxBatch = 20): TelemetrySink {
  const buffer: FrontendTelemetryEvent[] = [];
  return {
    emit(event): void {
      buffer.push(event);
      if (buffer.length >= maxBatch) flush(buffer.splice(0, buffer.length));
    },
  };
}
