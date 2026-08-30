from __future__ import annotations

from dataclasses import dataclass, field


class ExecutionBudgetExceeded(RuntimeError):
    pass


class AgentLoopDetected(RuntimeError):
    pass


@dataclass(slots=True)
class LoopGuard:
    max_steps: int = 12
    max_same_action: int = 2
    _steps: int = 0
    _counts: dict[str, int] = field(default_factory=dict)

    def checkpoint(self, fingerprint: str, *, now: float, deadline_at: float) -> None:
        if now >= deadline_at:
            raise ExecutionBudgetExceeded("run_deadline_exceeded")
        self._steps += 1
        if self._steps > self.max_steps:
            raise ExecutionBudgetExceeded("max_agent_steps_exceeded")
        self._counts[fingerprint] = self._counts.get(fingerprint, 0) + 1
        if self._counts[fingerprint] > self.max_same_action:
            raise AgentLoopDetected("repeated_agent_action_detected")

    @property
    def steps(self) -> int:
        return self._steps
