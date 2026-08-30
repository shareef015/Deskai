from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


class MassAssignmentViolation(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FieldPolicy:
    allowed: frozenset[str]
    immutable: frozenset[str] = frozenset({"id", "tenant_id", "created_at", "created_by"})

    @classmethod
    def from_allowed(cls, allowed: Iterable[str]) -> "FieldPolicy":
        return cls(frozenset(allowed))


def accept_fields(payload: Mapping[str, object], policy: FieldPolicy) -> dict[str, object]:
    attempted_immutable = policy.immutable.intersection(payload)
    if attempted_immutable:
        raise MassAssignmentViolation("immutable_fields:" + ",".join(sorted(attempted_immutable)))
    unknown = set(payload).difference(policy.allowed)
    if unknown:
        raise MassAssignmentViolation("unexpected_fields:" + ",".join(sorted(unknown)))
    return {key: payload[key] for key in policy.allowed if key in payload}
