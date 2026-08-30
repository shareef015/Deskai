from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .approval import ApprovalGate
from .citations import CitationVerifier, GroundingBundle
from .langgraph_contract import PRODUCTION_GRAPH, assert_transition
from .loop_guard import LoopGuard
from .models import (
    ApprovalGrant,
    ExecutionEvent,
    ExecutionState,
    Incident,
    RemediationPlan,
    RunContext,
    ToolResult,
)
from .retrieval import GovernedRetriever
from .routing import AgentRoute, DeterministicAgentRouter
from .tools import GovernedMcpDispatcher


Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    state: ExecutionState
    plan: RemediationPlan
    grounding: GroundingBundle
    diagnosis: ToolResult
    remediation: ToolResult | None
    verification: ToolResult | None
    approval: ApprovalGrant | None
    events: tuple[ExecutionEvent, ...]


class DeskPilotExecutionEngine:
    def __init__(
        self,
        *,
        retriever: GovernedRetriever,
        tools: GovernedMcpDispatcher,
        approvals: ApprovalGate,
        clock: Clock,
    ) -> None:
        PRODUCTION_GRAPH.validate()
        self._retriever = retriever
        self._tools = tools
        self._approvals = approvals
        self._clock = clock
        self._router = DeterministicAgentRouter()
        self._citations = CitationVerifier()

    def _event(self, events: list[ExecutionEvent], state: ExecutionState, event_type: str, context: RunContext, **details: object) -> None:
        events.append(ExecutionEvent(len(events) + 1, state, event_type, context.tenant_id, context.run_id, details))

    def prepare(self, context: RunContext, incident: Incident) -> ExecutionOutcome:
        events: list[ExecutionEvent] = []
        guard = LoopGuard()
        context.require_tenant(incident.tenant_id)
        state = ExecutionState.INTAKE
        self._event(events, state, "incident_accepted", context, incident_id=incident.incident_id)

        next_state = ExecutionState.RETRIEVING
        assert_transition(state, next_state)
        state = next_state
        guard.checkpoint("retrieve", now=self._clock(), deadline_at=context.deadline_at)
        retrieval = self._retriever.retrieve(context, incident)
        self._event(events, state, "evidence_retrieved", context, count=len(retrieval.evidence), blocked=len(retrieval.blocked_chunks))

        next_state = ExecutionState.GROUNDING
        assert_transition(state, next_state)
        state = next_state
        guard.checkpoint("ground", now=self._clock(), deadline_at=context.deadline_at)
        grounding = self._citations.build(context, retrieval.evidence)
        self._event(events, state, "citations_verified", context, citations=len(grounding.citations))

        next_state = ExecutionState.ROUTING
        assert_transition(state, next_state)
        state = next_state
        guard.checkpoint("route", now=self._clock(), deadline_at=context.deadline_at)
        route = self._router.route(context, incident)
        plan = self._router.plan(context, incident, route)
        self._event(events, state, "agent_routed", context, agent=route.agent_name)

        next_state = ExecutionState.DIAGNOSING
        assert_transition(state, next_state)
        state = next_state
        guard.checkpoint(route.diagnostic_tool, now=self._clock(), deadline_at=context.deadline_at)
        diagnosis = self._tools.execute(
            context,
            tool_name=route.diagnostic_tool,
            domain=incident.domain.value,
            resource_id=incident.device_id,
            args={"incident_id": incident.incident_id},
            now=self._clock(),
        )
        self._event(events, state, "diagnostic_completed", context, tool=route.diagnostic_tool, ok=diagnosis.ok)

        next_state = ExecutionState.AWAITING_APPROVAL
        assert_transition(state, next_state)
        state = next_state
        self._event(events, state, "approval_required", context, plan=plan.fingerprint)
        return ExecutionOutcome(state, plan, grounding, diagnosis, None, None, None, tuple(events))

    def approve_and_execute(
        self,
        context: RunContext,
        incident: Incident,
        prepared: ExecutionOutcome,
        *,
        approval: ApprovalGrant | None = None,
    ) -> ExecutionOutcome:
        if prepared.state is not ExecutionState.AWAITING_APPROVAL:
            raise ValueError("execution_not_awaiting_approval")
        context.require_tenant(incident.tenant_id)
        events = list(prepared.events)
        route: AgentRoute = self._router.route(context, incident)
        plan = prepared.plan
        if approval is None:
            approval = self._approvals.issue(context, plan, now=self._clock())
        self._approvals.consume(context, plan, approval.approval_id, now=self._clock())
        self._event(events, ExecutionState.AWAITING_APPROVAL, "approval_consumed", context, approval_id=approval.approval_id)

        assert_transition(ExecutionState.AWAITING_APPROVAL, ExecutionState.REMEDIATING)
        remediation = self._tools.execute(
            context,
            tool_name=route.remediation_tool,
            domain=incident.domain.value,
            resource_id=incident.device_id,
            args={"action": plan.action, "incident_id": incident.incident_id},
            now=self._clock(),
            approved=True,
        )
        self._event(events, ExecutionState.REMEDIATING, "remediation_completed", context, tool=route.remediation_tool, ok=remediation.ok)
        if not remediation.ok:
            return ExecutionOutcome(ExecutionState.FAILED, plan, prepared.grounding, prepared.diagnosis, remediation, None, approval, tuple(events))

        assert_transition(ExecutionState.REMEDIATING, ExecutionState.VERIFYING)
        verification = self._tools.execute(
            context,
            tool_name=route.verification_tool,
            domain=incident.domain.value,
            resource_id=incident.device_id,
            args={"incident_id": incident.incident_id},
            now=self._clock(),
        )
        self._event(events, ExecutionState.VERIFYING, "verification_completed", context, tool=route.verification_tool, ok=verification.ok)
        if verification.ok:
            assert_transition(ExecutionState.VERIFYING, ExecutionState.CLOSED)
            self._event(events, ExecutionState.CLOSED, "incident_closed", context, incident_id=incident.incident_id)
            state = ExecutionState.CLOSED
        else:
            assert_transition(ExecutionState.VERIFYING, ExecutionState.DIAGNOSING)
            self._event(events, ExecutionState.DIAGNOSING, "verification_failed_retriage_required", context)
            state = ExecutionState.DIAGNOSING
        return ExecutionOutcome(state, plan, prepared.grounding, prepared.diagnosis, remediation, verification, approval, tuple(events))
