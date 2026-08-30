from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping


DEFAULT_DEMO_STATE: dict[str, object] = {
    "scenario": "baseline",
    "incidents": [],
    "approvals": [],
    "device_faults": {},
    "audit_sequence": 0,
    "active_persona": None,
}


def state_fingerprint(state: Mapping[str, object]) -> str:
    return sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ResetResult:
    before: str
    after: str
    baseline: str
    restored: bool


class DemoResetController:
    def __init__(self, baseline: Mapping[str, object] | None = None) -> None:
        self._baseline = deepcopy(dict(baseline or DEFAULT_DEMO_STATE))
        self._state = deepcopy(self._baseline)
        self._baseline_fingerprint = state_fingerprint(self._baseline)

    @property
    def state(self) -> dict[str, object]:
        return deepcopy(self._state)

    @property
    def baseline_fingerprint(self) -> str:
        return self._baseline_fingerprint

    def mutate(self, *, scenario: str, incident_id: str, device_id: str, fault: str, persona_id: str) -> None:
        incidents = list(self._state.get("incidents", []))
        incidents.append(incident_id)
        faults = dict(self._state.get("device_faults", {}))
        faults[device_id] = fault
        self._state.update(
            {
                "scenario": scenario,
                "incidents": incidents,
                "device_faults": faults,
                "audit_sequence": int(self._state.get("audit_sequence", 0)) + 1,
                "active_persona": persona_id,
            }
        )

    def record_approval(self, approval_id: str) -> None:
        approvals = list(self._state.get("approvals", []))
        approvals.append(approval_id)
        self._state["approvals"] = approvals
        self._state["audit_sequence"] = int(self._state.get("audit_sequence", 0)) + 1

    def reset(self) -> ResetResult:
        before = state_fingerprint(self._state)
        self._state = deepcopy(self._baseline)
        after = state_fingerprint(self._state)
        return ResetResult(before, after, self._baseline_fingerprint, after == self._baseline_fingerprint)
