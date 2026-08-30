from __future__ import annotations

from .models import DemoRole, SyntheticPersona


DEMO_PERSONAS: tuple[SyntheticPersona, ...] = (
    SyntheticPersona(
        "recruiter-demo",
        "tenant-a",
        "Recruiter Demo Viewer",
        DemoRole.RECRUITER,
        frozenset({"demo:view"}),
    ),
    SyntheticPersona(
        "service-desk-demo",
        "tenant-a",
        "Service Desk Engineer",
        DemoRole.SERVICE_DESK,
        frozenset({"ai:diagnose", "remediation:approve", "remediation:execute", "demo:reset"}),
    ),
    SyntheticPersona(
        "approver-demo",
        "tenant-a",
        "Remediation Approver",
        DemoRole.APPROVER,
        frozenset({"ai:diagnose", "remediation:approve", "remediation:execute"}),
    ),
    SyntheticPersona(
        "reviewer-demo",
        "tenant-a",
        "Security Reviewer",
        DemoRole.REVIEWER,
        frozenset({"ai:diagnose", "demo:view"}),
    ),
)


class DemoPersonaError(PermissionError):
    pass


class DemoPersonaRegistry:
    def __init__(self, personas: tuple[SyntheticPersona, ...] = DEMO_PERSONAS) -> None:
        self._personas = {persona.persona_id: persona for persona in personas}

    def select(self, persona_id: str, *, demo_mode: bool, requested_tenant: str | None = None) -> SyntheticPersona:
        if not demo_mode:
            raise DemoPersonaError("synthetic_persona_disabled_outside_demo_mode")
        persona = self._personas.get(persona_id)
        if persona is None or not persona.synthetic:
            raise DemoPersonaError("unknown_synthetic_persona")
        if requested_tenant is not None and requested_tenant != persona.tenant_id:
            raise DemoPersonaError("synthetic_persona_cross_tenant_denied")
        return persona

    def all(self) -> tuple[SyntheticPersona, ...]:
        return tuple(self._personas.values())
