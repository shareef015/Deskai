from __future__ import annotations

from dataclasses import dataclass

from .models import Incident, IncidentDomain, RemediationPlan, RunContext


@dataclass(frozen=True, slots=True)
class AgentRoute:
    agent_name: str
    diagnostic_tool: str
    remediation_tool: str
    verification_tool: str


class DeterministicAgentRouter:
    """Production routing is explicit, bounded and auditable rather than free-form agent delegation."""

    _routes = {
        IncidentDomain.OUTLOOK: AgentRoute(
            "outlook-support-agent",
            "mcp.outlook.diagnose",
            "mcp.outlook.remediate",
            "mcp.outlook.verify",
        ),
        IncidentDomain.PRINTER: AgentRoute(
            "printer-support-agent",
            "mcp.printer.diagnose",
            "mcp.printer.remediate",
            "mcp.printer.verify",
        ),
    }

    def route(self, context: RunContext, incident: Incident) -> AgentRoute:
        context.require_tenant(incident.tenant_id)
        return self._routes[incident.domain]

    def plan(self, context: RunContext, incident: Incident, route: AgentRoute) -> RemediationPlan:
        context.require_capability("ai:diagnose")
        text = f"{incident.title} {incident.description}".lower()
        if incident.domain is IncidentDomain.PRINTER:
            action = "restart_spooler" if "spool" in text or "queue" in text else "refresh_printer_connection"
        else:
            action = "restart_outlook" if "crash" in text or "slow" in text else "refresh_outlook_sync"
        return RemediationPlan(
            action=action,
            tool_name=route.remediation_tool,
            resource_id=incident.device_id,
            reason=f"deterministic_plan_for:{incident.domain.value}",
            risk="medium",
            requires_approval=True,
        )
