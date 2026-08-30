from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_ai_pipeline.approval import ApprovalGate
from deskpilot_ai_pipeline.fixtures import synthetic_corpus, synthetic_tools
from deskpilot_ai_pipeline.models import Incident, IncidentDomain, RunContext
from deskpilot_ai_pipeline.orchestration import DeskPilotExecutionEngine
from deskpilot_ai_pipeline.retrieval import GovernedRetriever
from deskpilot_llmops.integration import InstrumentedExecutionEngine
from deskpilot_llmops.telemetry import TelemetryRecorder


class Clock:
    def __call__(self) -> float:
        return 100.0


def ctx() -> RunContext:
    return RunContext("run-observed", "tenant-a", "user-1", "session-1", frozenset({"ai:diagnose", "remediation:approve", "remediation:execute"}), 100, 300, "corr-observed")


class ObservedPipelineTests(unittest.TestCase):
    def engine(self) -> tuple[InstrumentedExecutionEngine, TelemetryRecorder]:
        telemetry = TelemetryRecorder()
        engine = DeskPilotExecutionEngine(retriever=GovernedRetriever(synthetic_corpus()), tools=synthetic_tools(), approvals=ApprovalGate(), clock=Clock())
        return InstrumentedExecutionEngine(engine, telemetry), telemetry

    def test_full_printer_path_produces_correlated_stage_spans(self) -> None:
        engine, telemetry = self.engine()
        incident = Incident("p1", "tenant-a", IncidentDomain.PRINTER, "Printer queue stuck", "spooler queue stuck", "pc-1")
        prepared = engine.prepare(ctx(), incident)
        outcome = engine.approve_and_execute(ctx(), incident, prepared)
        self.assertEqual(outcome.state.value, "closed")
        stages = {span.stage for span in telemetry.spans}
        self.assertTrue({"api", "rag", "langgraph", "mcp", "hitl", "workflow"}.issubset(stages))
        self.assertEqual(len({span.trace_id for span in telemetry.spans}), 1)
        self.assertTrue(all(log.correlation_id == "corr-observed" for log in telemetry.logs))

    def test_ai_citation_metric_is_recorded(self) -> None:
        engine, telemetry = self.engine()
        incident = Incident("o1", "tenant-a", IncidentDomain.OUTLOOK, "Outlook disconnected", "mailbox sync disconnected", "pc-2")
        engine.prepare(ctx(), incident)
        self.assertGreaterEqual(telemetry.metrics.latest("deskpilot.ai.citation.count") or 0, 1)

    def test_no_sensitive_values_in_recorded_attributes(self) -> None:
        telemetry = TelemetryRecorder()
        root = telemetry.root_context(correlation_id="c", tenant_id="t", run_id="r")
        telemetry.record_span(root, name="llm", stage="llm", started_at=1, ended_at=2, attributes={"access_token": "secret", "email": "user@example.com"})
        attrs = telemetry.spans[0].attributes
        self.assertEqual(attrs["access_token"], "[REDACTED]")
        self.assertNotIn("user@example.com", str(attrs))


if __name__ == "__main__":
    unittest.main()
