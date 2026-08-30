from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .models import RunContext, ToolResult


class ToolAuthorizationError(RuntimeError):
    pass


class ToolExecutionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    required_capability: str
    mutating: bool
    timeout_seconds: float
    allowed_domains: frozenset[str]


ToolHandler = Callable[[RunContext, str, Mapping[str, object]], ToolResult]


class GovernedMcpDispatcher:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler

    def execute(
        self,
        context: RunContext,
        *,
        tool_name: str,
        domain: str,
        resource_id: str,
        args: Mapping[str, object],
        now: float,
        approved: bool = False,
    ) -> ToolResult:
        spec = self._specs.get(tool_name)
        handler = self._handlers.get(tool_name)
        if spec is None or handler is None:
            raise ToolAuthorizationError("tool_not_registered")
        if domain not in spec.allowed_domains:
            raise ToolAuthorizationError("tool_domain_denied")
        context.require_capability(spec.required_capability)
        if spec.mutating and not approved:
            raise ToolAuthorizationError("mutating_tool_requires_approval")
        remaining = context.deadline_at - now
        if remaining <= 0:
            raise ToolExecutionError("tool_run_deadline_exceeded")
        if spec.timeout_seconds > remaining:
            raise ToolExecutionError("insufficient_tool_time_budget")
        result = handler(context, resource_id, args)
        context.require_tenant(result.tenant_id)
        if result.resource_id != resource_id:
            raise ToolExecutionError("tool_resource_binding_mismatch")
        return result

    def execute_with_fallback(
        self,
        context: RunContext,
        *,
        primary_tool: str,
        fallback_tool: str | None,
        domain: str,
        resource_id: str,
        args: Mapping[str, object],
        now: float,
    ) -> ToolResult:
        """Bounded read-only fallback. Mutating tools are never silently substituted."""
        primary = self._specs.get(primary_tool)
        if primary is None:
            raise ToolAuthorizationError("tool_not_registered")
        if primary.mutating:
            raise ToolAuthorizationError("mutating_tool_fallback_forbidden")
        try:
            return self.execute(
                context,
                tool_name=primary_tool,
                domain=domain,
                resource_id=resource_id,
                args=args,
                now=now,
            )
        except ToolExecutionError:
            if fallback_tool is None:
                raise
            fallback = self._specs.get(fallback_tool)
            if fallback is None:
                raise ToolAuthorizationError("fallback_tool_not_registered")
            if fallback.mutating:
                raise ToolAuthorizationError("mutating_fallback_forbidden")
            return self.execute(
                context,
                tool_name=fallback_tool,
                domain=domain,
                resource_id=resource_id,
                args=args,
                now=now,
            )
