from __future__ import annotations

from dataclasses import dataclass


class CapacityExceeded(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ConcurrencyLease:
    tenant_id: str
    workload: str


class ConcurrencyGovernor:
    """Deterministic in-process model of distributed concurrency policy.

    Production deployments should back this policy with Redis/queue/workload primitives.
    """

    def __init__(self, *, limits: dict[str, int], tenant_share_max: float = 0.5) -> None:
        if not limits or any(value <= 0 for value in limits.values()):
            raise ValueError("positive concurrency limits are required")
        if not 0 < tenant_share_max <= 1:
            raise ValueError("tenant_share_max must be in (0, 1]")
        self._limits = dict(limits)
        self._tenant_share_max = tenant_share_max
        self._active: dict[str, int] = {key: 0 for key in limits}
        self._tenant_active: dict[tuple[str, str], int] = {}

    def acquire(self, *, tenant_id: str, workload: str) -> ConcurrencyLease:
        if workload not in self._limits:
            raise KeyError(workload)
        limit = self._limits[workload]
        if self._active[workload] >= limit:
            raise CapacityExceeded(f"capacity_exhausted:{workload}")
        tenant_cap = max(1, int(limit * self._tenant_share_max))
        key = (tenant_id, workload)
        if self._tenant_active.get(key, 0) >= tenant_cap:
            raise CapacityExceeded(f"tenant_share_exhausted:{workload}")
        self._active[workload] += 1
        self._tenant_active[key] = self._tenant_active.get(key, 0) + 1
        return ConcurrencyLease(tenant_id, workload)

    def release(self, lease: ConcurrencyLease) -> None:
        key = (lease.tenant_id, lease.workload)
        active = self._tenant_active.get(key, 0)
        if active <= 0:
            raise RuntimeError("lease_not_active")
        self._tenant_active[key] = active - 1
        self._active[lease.workload] -= 1

    def utilization(self, workload: str) -> float:
        return self._active[workload] / self._limits[workload]
