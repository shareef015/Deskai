from __future__ import annotations

from dataclasses import dataclass

from deskpilot_ai_pipeline.approval import ApprovalGate
from deskpilot_ai_pipeline.fixtures import synthetic_corpus, synthetic_tools
from deskpilot_ai_pipeline.models import ExecutionState, Incident, IncidentDomain, RunContext
from deskpilot_ai_pipeline.orchestration import DeskPilotExecutionEngine
from deskpilot_ai_pipeline.retrieval import GovernedRetriever

from .models import DemoScenario, ScenarioExpectation, ScenarioResult, SyntheticPersona
from .reset import DemoResetController


class DeterministicClock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


@dataclass(frozen=True, slots=True)
class DemoConversation:
    greeting: str
    intake_question: str
    permission_prompt: str
    closure_message: str


def service_desk_script() -> DemoConversation:
    return DemoConversation(
        greeting="Hi, good day. Welcome to DeskPilot AI Service Desk.",
        intake_question="How can I help you today?",
        permission_prompt="May I run diagnostics on the affected Windows device and request approval before any remediation?",
        closure_message="Verification passed and the incident is ready for closure.",
    )


class RecruiterDemoRunner:
    def __init__(self, *, reset: DemoResetController | None = None) -> None:
        self.reset = reset or DemoResetController()
        self.clock = DeterministicClock()

    def _context(self, persona: SyntheticPersona, scenario: DemoScenario) -> RunContext:
        tenant_id = "tenant-a" if scenario.cross_tenant_context else scenario.tenant_id
        return RunContext(
            run_id=f"run-{scenario.scenario_id.lower()}",
            tenant_id=tenant_id,
            user_id=persona.persona_id,
            session_id=f"demo-session-{persona.persona_id}",
            capabilities=persona.capabilities,
            started_at=self.clock(),
            deadline_at=self.clock() + 300,
            correlation_id=f"corr-{scenario.scenario_id.lower()}",
        )

    def run(self, persona: SyntheticPersona, scenario: DemoScenario) -> ScenarioResult:
        self.reset.mutate(
            scenario=scenario.scenario_id,
            incident_id=scenario.incident_id,
            device_id=scenario.device_id,
            fault=scenario.title,
            persona_id=persona.persona_id,
        )
        context = self._context(persona, scenario)
        incident = Incident(
            incident_id=scenario.incident_id,
            tenant_id=scenario.tenant_id,
            domain=IncidentDomain(scenario.domain),
            title=scenario.title,
            description=scenario.description,
            device_id=scenario.device_id,
        )
        engine = DeskPilotExecutionEngine(
            retriever=GovernedRetriever(synthetic_corpus()),
            tools=synthetic_tools(verification_ok=scenario.verification_ok),
            approvals=ApprovalGate(),
            clock=self.clock,
        )

        if scenario.expected_final_state is ScenarioExpectation.DENIED:
            try:
                engine.prepare(context, incident)
            except PermissionError:
                return ScenarioResult(
                    scenario.scenario_id,
                    True,
                    "denied",
                    scenario.domain,
                    None,
                    0,
                    True,
                    False,
                    True,
                    None,
                    notes=("cross_tenant_context_denied_before_retrieval",),
                )
            return ScenarioResult(scenario.scenario_id, False, "unexpected_access", scenario.domain, None, 0, False, False, False, None)

        prepared = engine.prepare(context, incident)
        blocked_ids = {"x1", "x2"}
        grounded_ids = {evidence.chunk_id for evidence in prepared.grounding.evidence}
        injection_blocked = not bool(blocked_ids & grounded_ids)
        action_ok = prepared.plan.action == scenario.expected_action
        final = engine.approve_and_execute(context, incident, prepared)
        if final.approval is not None:
            self.reset.record_approval(final.approval.approval_id)
        expected_state = scenario.expected_final_state.value
        passed = (
            final.state.value == expected_state
            and action_ok
            and len(prepared.grounding.citations) > 0
            and injection_blocked
            and final.approval is not None
            and final.remediation is not None
            and final.remediation.ok
        )
        if scenario.expected_final_state is ScenarioExpectation.CLOSED:
            passed = passed and bool(final.verification and final.verification.ok)
        if scenario.expected_final_state is ScenarioExpectation.RETRIAGE:
            passed = passed and bool(final.verification is not None and not final.verification.ok)
            passed = passed and "incident_closed" not in {event.event_type for event in final.events}

        return ScenarioResult(
            scenario.scenario_id,
            passed,
            final.state.value,
            scenario.domain,
            prepared.plan.action,
            len(prepared.grounding.citations),
            injection_blocked,
            final.approval is not None,
            True,
            final.verification.ok if final.verification is not None else None,
            tuple(event.event_type for event in final.events),
        )
