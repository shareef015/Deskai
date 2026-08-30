from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_ai_pipeline.approval import ApprovalError, ApprovalGate
from deskpilot_ai_pipeline.fixtures import synthetic_corpus, synthetic_tools
from deskpilot_ai_pipeline.models import ExecutionState, Incident, IncidentDomain, RunContext
from deskpilot_ai_pipeline.orchestration import DeskPilotExecutionEngine
from deskpilot_ai_pipeline.retrieval import GovernedRetriever


class Clock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value
    def __call__(self) -> float:
        return self.value


def ctx(tenant: str = "tenant-a") -> RunContext:
    return RunContext("run-e2e", tenant, "engineer-1", "session-1", frozenset({"ai:diagnose", "remediation:approve", "remediation:execute"}), 100, 300, "corr-e2e")


class ProductionAiPathTests(unittest.TestCase):
    def engine(self, *, verification_ok: bool = True) -> DeskPilotExecutionEngine:
        return DeskPilotExecutionEngine(
            retriever=GovernedRetriever(synthetic_corpus()),
            tools=synthetic_tools(verification_ok=verification_ok),
            approvals=ApprovalGate(),
            clock=Clock(),
        )

    def test_printer_incident_reaches_verified_closure(self) -> None:
        incident = Incident("p-1", "tenant-a", IncidentDomain.PRINTER, "Printer queue stuck", "spooler queue stuck", "pc-01")
        engine = self.engine()
        prepared = engine.prepare(ctx(), incident)
        self.assertEqual(prepared.state, ExecutionState.AWAITING_APPROVAL)
        self.assertEqual(prepared.plan.action, "restart_spooler")
        self.assertGreater(len(prepared.grounding.citations), 0)
        outcome = engine.approve_and_execute(ctx(), incident, prepared)
        self.assertEqual(outcome.state, ExecutionState.CLOSED)
        self.assertTrue(outcome.remediation and outcome.remediation.ok)
        self.assertTrue(outcome.verification and outcome.verification.ok)
        self.assertEqual([event.sequence for event in outcome.events], list(range(1, len(outcome.events) + 1)))

    def test_outlook_incident_reaches_verified_closure(self) -> None:
        incident = Incident("o-1", "tenant-a", IncidentDomain.OUTLOOK, "Outlook disconnected", "mailbox sync disconnected", "pc-02")
        engine = self.engine()
        prepared = engine.prepare(ctx(), incident)
        self.assertEqual(prepared.plan.action, "refresh_outlook_sync")
        outcome = engine.approve_and_execute(ctx(), incident, prepared)
        self.assertEqual(outcome.state, ExecutionState.CLOSED)

    def test_failed_verification_routes_back_to_diagnosis_not_false_closure(self) -> None:
        incident = Incident("p-2", "tenant-a", IncidentDomain.PRINTER, "Printer offline", "printer connection offline", "pc-03")
        engine = self.engine(verification_ok=False)
        prepared = engine.prepare(ctx(), incident)
        outcome = engine.approve_and_execute(ctx(), incident, prepared)
        self.assertEqual(outcome.state, ExecutionState.DIAGNOSING)
        self.assertFalse(outcome.verification and outcome.verification.ok)
        self.assertNotIn("incident_closed", [event.event_type for event in outcome.events])

    def test_cross_tenant_execution_fails_before_ai_or_tool_execution(self) -> None:
        incident = Incident("p-3", "tenant-b", IncidentDomain.PRINTER, "Printer queue", "queue stuck", "pc-04")
        with self.assertRaises(PermissionError):
            self.engine().prepare(ctx("tenant-a"), incident)

    def test_prompt_injection_chunk_never_becomes_grounding(self) -> None:
        incident = Incident("p-4", "tenant-a", IncidentDomain.PRINTER, "Printer queue stuck", "spooler queue stuck", "pc-05")
        prepared = self.engine().prepare(ctx(), incident)
        self.assertNotIn("x1", [e.chunk_id for e in prepared.grounding.evidence])

    def test_approval_cannot_be_replayed_after_success(self) -> None:
        incident = Incident("p-5", "tenant-a", IncidentDomain.PRINTER, "Printer queue stuck", "spooler", "pc-06")
        engine = self.engine()
        prepared = engine.prepare(ctx(), incident)
        outcome = engine.approve_and_execute(ctx(), incident, prepared)
        self.assertIsNotNone(outcome.approval)
        with self.assertRaises(ApprovalError):
            engine.approve_and_execute(ctx(), incident, prepared, approval=outcome.approval)


if __name__ == "__main__":
    unittest.main()
