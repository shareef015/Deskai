from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoveryObjective:
    name: str
    rpo_seconds: int
    rto_seconds: int


@dataclass(frozen=True, slots=True)
class RecoveryObservation:
    data_loss_seconds: int
    recovery_seconds: int
    integrity_verified: bool


@dataclass(frozen=True, slots=True)
class RecoveryAssessment:
    passed: bool
    failures: tuple[str, ...]


def assess_recovery(objective: RecoveryObjective, observation: RecoveryObservation) -> RecoveryAssessment:
    failures: list[str] = []
    if observation.data_loss_seconds > objective.rpo_seconds:
        failures.append("rpo_exceeded")
    if observation.recovery_seconds > objective.rto_seconds:
        failures.append("rto_exceeded")
    if not observation.integrity_verified:
        failures.append("restore_integrity_not_verified")
    return RecoveryAssessment(not failures, tuple(failures))
