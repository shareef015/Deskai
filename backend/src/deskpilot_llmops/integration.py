from __future__ import annotations

from deskpilot_ai_pipeline.models import Incident, RunContext
from deskpilot_ai_pipeline.orchestration import DeskPilotExecutionEngine, ExecutionOutcome

from .telemetry import TelemetryRecorder


_STAGE_BY_EVENT = {
    "incident_accepted": "api",
    "evidence_retrieved": "rag",
    "citations_verified": "rag",
    "agent_routed": "langgraph",
    "diagnostic_completed": "mcp",
    "approval_required": "hitl",
    "approval_consumed": "hitl",
    "remediation_completed": "remediation",
    "verification_completed": "mcp",
    "incident_closed": "workflow",
    "verification_failed_retriage_required": "workflow",
}


class InstrumentedExecutionEngine:
    def __init__(self, engine: DeskPilotExecutionEngine, telemetry: TelemetryRecorder) -> None:
        self.engine = engine
        self.telemetry = telemetry

    def _record(self, context: RunContext, outcome: ExecutionOutcome) -> None:
        root = self.telemetry.root_context(correlation_id=context.correlation_id, tenant_id=context.tenant_id, run_id=context.run_id)
        for event in outcome.events:
            stage = _STAGE_BY_EVENT.get(event.event_type, "workflow")
            ts = context.started_at + (event.sequence / 1000.0)
            child = self.telemetry.record_span(root, name=event.event_type, stage=stage, started_at=ts, ended_at=ts + 0.001, attributes={"event.sequence": event.sequence, "execution.state": event.state.value, **dict(event.details)})
            self.telemetry.log(child, timestamp=ts + 0.001, severity="INFO", event_name=event.event_type, message=event.event_type, attributes={"execution.state": event.state.value})
        self.telemetry.metrics.record("deskpilot.ai.citation.count", len(outcome.grounding.citations), unit="{citation}", labels={"stage": "rag"})

    def prepare(self, context: RunContext, incident: Incident) -> ExecutionOutcome:
        outcome = self.engine.prepare(context, incident)
        self._record(context, outcome)
        return outcome

    def approve_and_execute(self, context: RunContext, incident: Incident, prepared: ExecutionOutcome, **kwargs: object) -> ExecutionOutcome:
        outcome = self.engine.approve_and_execute(context, incident, prepared, **kwargs)
        # Only record newly added events to avoid double-counting prepare events.
        root = self.telemetry.root_context(correlation_id=context.correlation_id, tenant_id=context.tenant_id, run_id=context.run_id)
        for event in outcome.events[len(prepared.events):]:
            stage = _STAGE_BY_EVENT.get(event.event_type, "workflow")
            ts = context.started_at + (event.sequence / 1000.0)
            child = self.telemetry.record_span(root, name=event.event_type, stage=stage, started_at=ts, ended_at=ts + 0.001, attributes={"event.sequence": event.sequence, "execution.state": event.state.value, **dict(event.details)})
            self.telemetry.log(child, timestamp=ts + 0.001, severity="INFO", event_name=event.event_type, message=event.event_type, attributes={"execution.state": event.state.value})
        return outcome
